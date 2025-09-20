from typing import List

from kink import di
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import loguru

from config import Master


def construct_agent_prompt(agent_entry, agent_name, **kwargs):
    """
    Construct agent prompt
    :param agent_entry:
    :param agent_name:
    :return: prompt,agent_args,template_prompt
    """
    agent_work = agent_entry.__doc__ + "\n" + kwargs.get("system_prompt", "")
    kwargs.pop("system_prompt", None)
    agent_args = kwargs
    template_prompt = f"You are {agent_name},your work: {agent_work}"
    template_prompt = Master.get("prefix") + template_prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Your name is {agent_name}. {template_prompt}"),
        ("user", "{input}")
    ])
    return prompt, agent_args, template_prompt


def agent_scheduler(agent_entry, agent_name, **kwargs):
    """
    Call agent with agent_entry and agent_name
    :param agent_entry:
    :param agent_name:
    :return:
    """
    llm = di['llm']
    prompt, agent_args, template_prompt = construct_agent_prompt(agent_entry, agent_name, **kwargs)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    response = chain.invoke(
        {"input": f"Your args: {agent_args}", "agent_name": agent_name, "template_prompt": template_prompt})
    return response


async def async_agent_scheduler(agent_entry, agent_name, **kwargs):
    """
    Call agent with agent_entry and agent_name
    :param agent_entry:
    :param agent_name:
    :return:
    """
    llm = di['llm']
    prompt, agent_args, template_prompt = construct_agent_prompt(agent_entry, agent_name, **kwargs)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    response = chain.astream(
        {"input": f"Your args: {agent_args}", "agent_name": agent_name, "template_prompt": template_prompt})
    chunks = []
    async for chunk in response:
        chunks.append(chunk)
        print(chunk, end="")
        if check_closed_function_calls("".join(chunks)):
            break
    return "".join(chunks)


def check_closed_function_calls(string):
    """
    Check if there are closed function calls in the chunks
    :return:
    """
    return True if (string.count("%%") == 2) else False
