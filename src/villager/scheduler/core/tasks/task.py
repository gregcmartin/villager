from asyncio import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import kink
import loguru
from kink import inject, di
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from scheduler.core.Thought import Thought
from scheduler.core.mcp_client.mcp_client import McpClient
from scheduler.core.schemas.schemas import TaskModel, NeedBranchModel, TaskExecuteStatusModel, \
    TaskModelOut, TaskStatus, TaskModelOutList, strip_task_model_out
from scheduler.core.schemas.structure.ToT import TaskObject
from scheduler.core.schemas.structure.task_relation_manager import Node, TaskRelationManager, Direction
from scheduler.core.schemas.works.PydanticSafetyParser import chat_with_safety_pydantic_output_parser
from scheduler.core.tasks.exceptions.task_exceptions import TaskNeedTurningException, TaskImpossibleException
from tools.func.retry_decorator import retry


class TaskNode(Node):
    @kink.inject
    def __init__(
            self,
            task_model: TaskModel,
            trm: TaskRelationManager,
            mcp_client: McpClient,
            graph_name: str = 'default_graph_name',
            taskId: str = None,
    ):
        """
        Task class's init func.
        :param task_model: TaskModel
        :param trm: TRM obj.
        """

        super().__init__()
        self.task_pydantic_model = TaskObject(
            task_model=task_model,
            task_out_model=None,
            task_status_model=TaskStatus.PENDING
        )
        self.taskId = taskId
        self._trm = trm
        self.task = task_model
        self.mcp_client = mcp_client
        self.abstract = task_model.abstract
        self.description = task_model.description
        self.verification = task_model.verification
        loguru.logger.debug(f"Task: `{self.abstract}` has been created.")
        self._trm.add_task(self)
        self.graph_name = graph_name

        self._replan_counter = 0

    def __str__(self):
        masked_task_pydantic_model = self.task_pydantic_model
        masked_task_pydantic_model.task_model = TaskModel(
            abstract=masked_task_pydantic_model.task_model.abstract,
            description='[MASKED]',
            verification=masked_task_pydantic_model.task_model.verification,
        )
        return f"Task:{masked_task_pydantic_model}\n"

    def _flush_graph(self):
        """
        Flush the graph.
        :return:
        """
        self._trm.draw_graph(self.graph_name)

    def branch_and_execute(self, branch_requirement: NeedBranchModel) -> List[TaskModelOut]:
        """
        The worker need to do the branch task.
        :return:
        """
        loguru.logger.debug('Entry branch_and_execute.')
        task_chain = branch_requirement.task_chain
        # If has_dependency is True, execute sequentially; if False, run multi-threaded and wait for all results to finish before returning together, other logic remains the same

        tasks_classed: List[TaskNode] = []
        task_chain_output: List[TaskModelOut] | None = []
        loguru.logger.debug('branch_and_execute inited.')
        for subtask in task_chain.tasks:
            subtask = TaskNode(task_model=subtask, trm=self._trm, mcp_client=self.mcp_client,
                               graph_name=self.graph_name)
            tasks_classed.append(subtask)
        loguru.logger.debug('subtask...')
        self._trm.add_sub_tasks(current_task=self, sub_task=tasks_classed)

        for subtask in tasks_classed:
            try:
                task_chain_output.append(subtask.execute())
            except TaskImpossibleException as e:
                raise e
            except Exception as e:
                raise e

        return task_chain_output

    def direct_execute(self, advices, articles) -> TaskModelOut:
        """
        The worker do the task.
        :return:
        """
        loguru.logger.info(f"Task {self.task_pydantic_model} is working, articles: {articles}")
        self.task_pydantic_model = self.task_pydantic_model.copy(update={
            "task_status_model": TaskStatus.WORKING
        })

        max_try = 3
        for i in range(max_try):
            try:
                result = self.run_mcp_agent(articles=articles, advices=advices)
                if self.check_task_result(result):
                    result: TaskModelOut = self.digest_result_to_abstract(result=result)
                    self.task_pydantic_model = self.task_pydantic_model.copy(update={
                        "task_status_model": TaskStatus.SUCCESS,
                        "task_out_model": result
                    })
                    loguru.logger.success(f"Task {self.task_pydantic_model} is successful, result: {result}")
                    return result
            except TaskNeedTurningException as e:
                advices += f"You have already tried this task but failed. Here are suggestions for this execution: {e}"
            except TaskImpossibleException as e:
                self.task_pydantic_model = self.task_pydantic_model.copy(update={
                    "task_status_model": TaskStatus.ERROR,
                })
                raise e
            except Exception as e:
                raise e
        raise TaskImpossibleException(f"This task has been attempted {max_try} times, all unsuccessful")

    def execute(self, rebranch_prompt='') -> TaskModelOut:
        """
        The task's core.
        There are lots of thoughts in the villager.
        :return:
        """
        loguru.logger.warning(f'task_id: {self.id} {self.task_pydantic_model}')
        articles = ''
        advices = ''
        upper_chain: List[Node] = self._trm.get_upper_import_node_simple(self, window_n=3, window_m=6)

        if len(upper_chain) > 0:
            # Contains upper-level or same-level prerequisite tasks
            advices = f'Your current task is a subtask split from a parent task. Below I will provide you with the upstream task nodes of your current task, representing the relationship from parent node to adjacent node from top to bottom:'  # Override
            upper_chain.reverse()  # Stack order reversal
            for upper_node in upper_chain:
                advices += f'\n{upper_node.task_pydantic_model}'
        advices += f'\n{rebranch_prompt}'

        branch_requirement: NeedBranchModel = self.check_branching_requirement(advice=advices)
        loguru.logger.debug('branch_requirement done')
        self._flush_graph()
        loguru.logger.debug('flush_graph done')
        if len(branch_requirement.task_chain.tasks) > 0:
            try:
                _task_model_out = self.digest_task_model_out(self.branch_and_execute(branch_requirement))
                self.task_pydantic_model.task_out_model = _task_model_out
                return _task_model_out
            except TaskImpossibleException as e:
                # If lower-level task generates impossible task error, catch at this level and reassign task branch
                loguru.logger.warning(f"Task {self.id} {self.task_pydantic_model} is impossible, replan it.")
                _lower_chain = self._trm.get_lower_chain_simple(self, 1)
                assert len(_lower_chain) > 0, f"Child node of {self.id} failed, but no child node was found"
                loguru.logger.debug(f'Removing {_lower_chain}[0]: {_lower_chain[0]}')
                self._trm.remove_node(_lower_chain[0])  # If a node has both down and right direction child nodes, it will get the down node first, so taking the first one is always the node that should be deleted
                return self.execute()
        else:
            _direct_execute_result = self.direct_execute(advices, articles)
            self.task_pydantic_model = self.task_pydantic_model.copy(update={
                "task_status_model": TaskStatus.SUCCESS,
                "task_out_model": _direct_execute_result
            })
            return _direct_execute_result

    def digest_task_model_out(self, input_task_model_out_list: List[TaskModelOut]) -> TaskModelOut:
        """
        Check the task's result is correct or not.
        :return:
        """
        loguru.logger.debug(f"Merging task results: {input_task_model_out_list};"
                            f"Parent node: {self.task_pydantic_model} {self.id}")

        pydantic_object = TaskModelOut
        model = di['llm']
        parser = PydanticOutputParser(pydantic_object=pydantic_object)
        promptTemplate = ChatPromptTemplate.from_messages([
            ("system", "{format_instructions}"
                       "You are an assistant. Please integrate and condense the task output list provided by the user into the task return result required by the parent node."
                       "Please note:"
                       "Do not attempt to actually execute tasks!"
             ),
            ("user",
             "Task output list:{task_model_out_list};Parent node content:{parent_node}")
        ])
        input_args = {
            "format_instructions": parser.get_format_instructions(),
            "task_model_out_list": TaskModelOutList(task_model_out_list=input_task_model_out_list),
            "parent_node": self
        }
        return chat_with_safety_pydantic_output_parser(model=model, input_args=input_args,
                                                       promptTemplate=promptTemplate,
                                                       schemas_model=pydantic_object)

    @retry(max_retries=5, delay=1)
    @inject
    def digest_result_to_abstract(self, result: str, llm):
        """
        Focus on summary of mission results.
        :return:
        """
        pydantic_object = TaskModelOut
        model = llm
        parser = PydanticOutputParser(pydantic_object=pydantic_object)
        promptTemplate = ChatPromptTemplate.from_messages([
            ("system", "{format_instructions};"
                       "You are a summarizer responsible for summarizing the result report below into valuable content (that the task is concerned with). The return format must strictly follow the above requirements;"
                       "Essential resources created by terminals, browsers, etc. must be returned intact, such as terminal IDs, for subsequent use"
                       "Only factual content that appears in the summary article is allowed, no assumptions or secondary inferences are permitted;"
                       "(Do not attempt to actually execute this task!)"
             ),
            ("user", "Result report:{result_report};Corresponding task for this result:{task}")
        ])
        input_args = {"result_report": result,
                      "task": self.task,
                      "format_instructions": parser.get_format_instructions(),
                      }
        return strip_task_model_out(
            input_task_model_out=chat_with_safety_pydantic_output_parser(
                model=model,
                input_args=input_args,
                promptTemplate=promptTemplate,
                schemas_model=pydantic_object
            )
        )

    @retry(max_retries=5, delay=1)
    @inject
    def check_branching_requirement(self, llm, advice=''):
        """
        The thought think about do we need branch for this task.
        :param llm: Dependency Injection's llm object
        :param advice:
        :return:
        """
        pydantic_object = NeedBranchModel
        model = llm
        parser = PydanticOutputParser(pydantic_object=pydantic_object)
        promptTemplate = ChatPromptTemplate.from_messages([
            ("system", "{format_instructions};"
                       """You are a planner. Please comprehensively judge based on the user's questions and upper-level task nodes whether we need to decompose this task to complete it.

Please note:

1. Our executor has terminal execution and browser calling capabilities. Please plan subtasks reasonably based on these capabilities
2. If needed, please provide task chains in order and ensure task continuity
3. If not needed, please return a chain of length 0
4. Should only follow the intent of the user-provided task. Upper nodes are for reference only. Do not arbitrarily subdivide tasks to implement higher-level parent node intentions to avoid losing information
5. Please describe each task as comprehensively as possible, including the task's establishment reason, necessity, environment and other information
6. Please try to plan using existing tools and the simplest and fastest solutions
7. Should try to ensure planning reliability, minimize exploratory tasks. If lacking information, try searching online first
8. When planning tasks, if there is content you are unsure about or don't understand, please first plan a node to understand and search, ensuring understanding before practice
9. For network security tasks, please try to use existing tools, such as using nuclei directly for vulnerability scanning, msfconsole for system vulnerabilities, etc.
"""
             ),
            ("user",
             "Task summary:{abstract};Task description:{description};As your execution reference, your upper-level or same-level prerequisite tasks are as follows (for reference only, do not execute):{advice};")
        ])
        input_args = {"abstract": self.abstract,
                      "description": self.description,
                      "format_instructions": parser.get_format_instructions(),
                      "advice": advice,
                      }
        res = chat_with_safety_pydantic_output_parser(model=model, input_args=input_args,
                                                      promptTemplate=promptTemplate,
                                                      schemas_model=pydantic_object)
        loguru.logger.debug(f"Task chain {res}")
        return res

    def run_mcp_agent(self, articles: str = '', advices: str = '',
                      prompt=r"""Please help me complete the following tasks and return the information that should be returned. During execution, the following principles should be followed:

1. Follow facts, do not assume
2. Return all necessary resources (such as downloaded file paths, terminal IDs after environment installation, etc.)
3. Do not refuse
4. Do not execute too much content at once, do it step by step
5. Try to use existing tools and the simplest and fastest solutions
6. The provided tasks may not necessarily be completed, but regardless of whether they can be completed or not, a result of whether it is possible or not should be returned after attempting

The following is the content that needs to be completed:""") -> str:
        return self.mcp_client.execute(
            f'{prompt}Task summary:{self.abstract}\n'
            f'Task description:{self.description}\n'
            f'{articles};{advices};')

    def check_task_result(self, result: str):
        """
        Check the task's result is correct or not.
        :return:
        """
        pydantic_object = TaskExecuteStatusModel
        model = di['llm']
        parser = PydanticOutputParser(pydantic_object=pydantic_object)
        promptTemplate = ChatPromptTemplate.from_messages([
            ("system", "You are an assistant. Please comprehensively judge the status of this task based on the user's questions and another worker's execution results. The return format must strictly follow the following requirements {format_instructions};"
                       "Please note:"
                       "1. Do not attempt to actually execute tasks!"
                       "2. You have permission to call some functions. Another worker has the same permissions as you, which helps you judge their status. The function list will be provided below;"
             ),
            ("user",
             "Task summary:```{abstract}```;Task description:```{description}```;Execution result:```{result}```;Acceptance criteria:{verification}")
        ])
        input_args = {
            "format_instructions": parser.get_format_instructions(),
            "abstract": self.abstract,
            "description": self.description,
            "result": result,
            "verification": self.verification,
        }
        task_status_model = chat_with_safety_pydantic_output_parser(model=model, input_args=input_args,
                                                                    promptTemplate=promptTemplate,
                                                                    schemas_model=pydantic_object)
        if task_status_model.is_task_successful == 0:
            if task_status_model.is_task_impossible == 0:
                raise TaskNeedTurningException(task_status_model.explain)
            else:
                explain_str = f"Task:{self.abstract} execution failed, failure reason:{task_status_model.explain}"
                # Only impossible tasks will throw exceptions to parent tasks, so task summary needs to be clarified
                raise TaskImpossibleException(explain_str)
        else:
            return True
