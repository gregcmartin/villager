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
        # 如果has_dependency为True，那么顺序执行，如果为False，那么多线程运行，并等待所有结果结束后才一起返回，其余逻辑均相同

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
                advices += f"此任务你已经尝试过了，但是没有成功，以下是给此次执行的建议:{e}"
            except TaskImpossibleException as e:
                self.task_pydantic_model = self.task_pydantic_model.copy(update={
                    "task_status_model": TaskStatus.ERROR,
                })
                raise e
            except Exception as e:
                raise e
        raise TaskImpossibleException(f"此任务已经尝试{max_try}次了，均没有成功")

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
            # 含有上级或平级的前置任务
            advices = f'你当前的任务是一个父任务中分出的子任务，以下我将提供给你当前任务的上游任务节点，从上到下代表从父节点到相邻节点的关系:'  # 覆盖
            upper_chain.reverse()  # 栈序翻转
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
                # 若下级任务产生任务不可能的错误，在此级捕获并重新分配任务分支
                loguru.logger.warning(f"Task {self.id} {self.task_pydantic_model} is impossible, replan it.")
                _lower_chain = self._trm.get_lower_chain_simple(self, 1)
                assert len(_lower_chain) > 0, f"{self.id}的子节点失败了，但是并没有找到子节点"
                loguru.logger.debug(f'Removing {_lower_chain}[0]: {_lower_chain[0]}')
                self._trm.remove_node(_lower_chain[0])  # 若一个节点同时有下和右方向的子节点，会先获取下节点，所以直接取第一个永远是应该删除的节点
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
        loguru.logger.debug(f"正在合并任务结果: {input_task_model_out_list};"
                            f"父节点: {self.task_pydantic_model} {self.id}")

        pydantic_object = TaskModelOut
        model = di['llm']
        parser = PydanticOutputParser(pydantic_object=pydantic_object)
        promptTemplate = ChatPromptTemplate.from_messages([
            ("system", "{format_instructions}"
                       "你是一名助手，请根据用户提供的任务输出列表整合浓缩成父节点所需要的任务返回结果"
                       "请注意:"
                       "不要尝试去实际执行任务!"
             ),
            ("user",
             "任务输出列表:{task_model_out_list};父节点内容:{parent_node}")
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
                       "你是一名摘要员，负责将下文的结果报告摘要为有价值的(task所关注的)内容，返回格式请严格遵循以上要求;"
                       "需要将终端、浏览器等创建的必要的资源原封不动的返回，如终端id等，以备后续使用"
                       "只允许摘要文章中出现过的事实内容, 不允许添加任何假设或二次推断的内容;"
                       "(不要尝试去实际执行此任务!)"
             ),
            ("user", "结果报告:{result_report};此结果的对应任务:{task}")
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
                       """你是一名规划师，请根据用户的问题和上级任务节点综合判断，我们是否需要分解该任务才能完成这个任务

请注意:

1. 我们的执行者拥有终端执行和浏览器调用的能力，请根据其能力合理规划子任务
2. 如果需要，请按照顺序提供任务链，并保证任务的连续性
3. 如果不需要，请返回长度为0的链
4. 应只遵守用户提供任务的意图，再往上的节点只供参考，不要随意细分任务去实现更上层的父节点的意图，避免丢失一些信息
5. 请尽可能全面的对每一个任务进行描述，包括任务的设立原因、必要性、环境等信息
6. 请尽量规划使用现有的工具和最简单最快速的方案
7. 应尽量保证规划的可靠性，尽量少规划探索类任务，如缺少什么信息，可以先尝试上网搜索
8. 规划任务时，若存在没有把握或者不了解的内容，请先规划出一个去了解、搜索的节点，保证理解了内容后再去实践
9. 网络安全类任务请尽量使用现有工具，如漏扫直接使用nuclei，系统漏洞直接使用msfconsole等
"""
             ),
            ("user",
             "任务简述:{abstract};任务描述:{description};作为你的执行参考，你的上级或平级的前置任务如下(仅供参考，不要执行):{advice};")
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
                      prompt=r"""请你帮我完成以下任务，并返回应返回的信息，在执行中应满足以下原则:

1. 遵从事实，不要假设
2. 返回一切所必要返回的资源（比如下载文件的path、安装环境后的terminalID等）
3. 不要拒绝
4. 不要一次执行过多内容，要边做边看
5. 尽量使用现有的工具和最简单最快速的方案
6. 提供的任务并不一定可以完成，但是无论可不可以都要在尝试之后返回一个可以或不可以的结果

以下是需要完成的内容:""") -> str:
        return self.mcp_client.execute(
            f'{prompt}任务摘要:{self.abstract}\n'
            f'任务描述:{self.description}\n'
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
            ("system", "你是一名助手，请根据用户的问题和另一位工人的执行结果综合判断此任务状态如何，返回格式请严格遵循以下要求{format_instructions};"
                       "请注意:"
                       "1. 不要尝试去实际执行任务!"
                       "2. 你有权限调用一些函数，另一位工人和你有同等权限，这有助于你判断其状态，下文会给你函数列表;"
             ),
            ("user",
             "任务简述:```{abstract}```;任务描述:```{description}```;执行结果:```{result}```;验收标准:{verification}")
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
                explain_str = f"任务:{self.abstract}执行失败，失败原因:{task_status_model.explain}"
                # 只有不可能的任务才会向父任务抛出异常，所以需要明确任务简述
                raise TaskImpossibleException(explain_str)
        else:
            return True
