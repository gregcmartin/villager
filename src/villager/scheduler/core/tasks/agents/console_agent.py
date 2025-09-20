# -----------------------------------------------------
# 此文件定义了一个 ConsoleAgent 类，可直接连续的在控制台交互
# -----------------------------------------------------
from kink import inject
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferMemory

from scheduler.core.schemas.schemas import TaskModel


class ConsoleAgent:
    @inject
    def __init__(self, llm, task: TaskModel):
        self.conversation = ConversationChain(
            llm=llm, verbose=True, memory=ConversationBufferMemory()
        )

    def invoke(self):
        """
        交互式执行task，不需要检验
        :return:
        """
        ...
