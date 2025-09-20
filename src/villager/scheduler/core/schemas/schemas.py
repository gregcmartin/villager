from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class NeedRAGModel(BaseModel):
    isNeed: int = Field(description="Whether to query the knowledge base, 1 for needed, 0 for not needed")
    keywords: str = Field(description="Space-separated keywords")


class TaskStatus(Enum):
    PENDING = "pending"
    WORKING = "working"
    ERROR = "error"
    SUCCESS = "success"

    def __str__(self):
        """
        Let the class can be JSON serialized.
        :return:
        """
        return self.value


class TaskModel(BaseModel):
    abstract: str = Field(description="Task summary")
    description: str = Field(description="Complete task description")
    verification: str = Field(description="Task verification criteria (e.g., whether a response packet containing vulnerabilities is provided)")


class TaskModelOut(BaseModel):
    result_abstract: str = Field(description="Summary of task execution results")
    result: str = Field(description="Detailed information of task execution results")


class TaskModelOutList(BaseModel):
    task_model_out_list: List[TaskModelOut] = Field(description="List of TaskModelOut objects")


class TaskChainModel(BaseModel):
    tasks: List[TaskModel] = Field(description="Task list")


class NeedBranchModel(BaseModel):
    task_chain: TaskChainModel = Field(description="Single task node or task node chain")
    # has_dependency: bool = Field(description="Whether the node chain has mutual dependencies")


class TaskExecuteStatusModel(BaseModel):
    is_task_successful: int = Field(description="Whether this task is successfully completed, 1 for success, 0 for failure")
    is_task_impossible: int = Field(
        description="If not successfully completed, is this task impossible to complete with your abilities, 1 for impossible, 0 for possible, do not easily return impossible.")
    explain: str = Field(
        description="If impossible to complete, explain the reasons for impossibility. If possible to complete, explain what problems exist in the task execution approach and how to correct them")


def strip_task_model_out(input_task_model_out: TaskModelOut) -> TaskModelOut:
    return TaskModelOut(
        result=input_task_model_out.result.replace('"', "'"),
        result_abstract=input_task_model_out.result_abstract.replace('"', "'")
    )
