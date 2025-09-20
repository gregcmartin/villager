import loguru

from scheduler.core.tools.common_tool import pyeval, os_execute_cmd
from scheduler.core.tools.agent_with_tools import tool_villager
from scheduler.toolschain.tools_manager import ToolsManager, extract_json_with_positions


class Thought:
    def __init__(self):
        ...
    def sync_chat_with_tool(self, **kwargs):
        """
        Chat with LLM with tools privilege.
        :param message:
        :return:
        """
        response_content = tool_villager(tools=self.tools_manager.list_func_json(), **kwargs)
        loguru.logger.debug(f"response_content: {response_content}")
        use_tools_situation = extract_json_with_positions(response_content)
        for tool in use_tools_situation:
            json_func_str = tool[0]
            res = self.tools_manager.NLP_unserialize(str(json_func_str))
            loguru.logger.debug(f"tools_execute_res: {res}")
            response_content = response_content.replace(str(tool[1]), str(res))
        loguru.logger.debug("response_content_with_tools: ", response_content)
        return response_content

    def async_chat_with_tool(self, **kwargs):
        """
        Chat with LLM with tools privilege.
        :param message:
        :return:
        """
        response_content = tool_villager(tools=self.tools_manager.list_func_json(), **kwargs)
        use_tools_situation = extract_json_with_positions(response_content)
        for tool in use_tools_situation:
            json_func_str = tool[0]
            res = self.tools_manager.NLP_unserialize(str(json_func_str))
            response_content = response_content.replace(str(tool[1]), str(res))
        return response_content
