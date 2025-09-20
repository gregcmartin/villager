# -----------------------------------------------------
# This file defines a ConsoleAgent class that can interact directly and continuously in the console
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
        Interactive task execution, no verification required
        :return:
        """
        ...
