import loguru
from langchain.output_parsers import OutputFixingParser
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.utils import Input
from pydantic import BaseModel

from config import Master
from scheduler.core.sharegpt_logger import log_sharegpt_conversation
from tools.logging import logging
from tools.args_wrap.loading import running_indicator


def chat_with_safety_pydantic_output_parser(model: BaseChatModel, input_args: Input, promptTemplate: ChatPromptTemplate,
                                            schemas_model: BaseModel) -> BaseModel:
    """
    Chat with Safety Pydantic Output Parser
    :param model:
    :param input_args:
    :param promptTemplate:
    :param schemas_model:
    :return: Pydantic Model

    Example:
            model = ChatOpenAI(
            temperature=0.0,
            model=Master.get("default_model"),
            base_url=Master.get("openai_api_endpoint"),
            api_key=Master.get("openai_api_key"),
        )
        parser = PydanticOutputParser(pydantic_object=TaskStatusModel)
        promptTemplate = ChatPromptTemplate.from_messages([
            ("system", "你是一名助手，请根据用户的问题和另一位工人的执行结果综合判断此任务状态如何，返回格式请严格遵循以下要求{format_instructions};"
                       "(不要尝试去实际执行任务!)"
                       "你有权限调用一些函数，另一位工人和你有同等权限，这有助于你判断其状态，下文会给你函数列表;"
             ),
            ("user", "任务简述:```{abstract}```;任务描述:```{description}```;执行结果:```{result}```;验收标准:{verification}"
                     "函数列表:{func_list}")
        ])
        func_list = self.tools_manager.list_func_json()
        input_args = {
            "format_instructions": parser.get_format_instructions(),
            "abstract": self.abstract,
            "description": self.description,
            "func_list": str(func_list),
            "result": result,
            "verification": self.verification,
        }
        task_status_model = ChatWithSafetyPydanticOutputParser(model=model, input_args=input_args,
                                                               promptTemplate=promptTemplate,
                                                               schemas_model=TaskStatusModel)
    """
    parser = PydanticOutputParser(pydantic_object=schemas_model)
    chain = promptTemplate | model

    raw_output = chain.invoke(input_args)

    _input_str = promptTemplate.format(**input_args)
    _output_str = str(raw_output.content)
    log_sharegpt_conversation(
        input_content=_input_str,
        output_content=_output_str,
        metadata={"model": Master.get("default_model"), "temperature": 0.95}
    )

    try:
        raw_output = _output_str
        schemas_model = parser.parse(raw_output)
    except OutputParserException as e:
        try:
            schemas_model = OutputFixingParser.from_llm(parser=parser, llm=model).parse(raw_output)
        except OutputParserException as e:
            return chat_with_safety_pydantic_output_parser(model=model, input_args=input_args,
                                                           promptTemplate=promptTemplate, schemas_model=schemas_model)
    return schemas_model
