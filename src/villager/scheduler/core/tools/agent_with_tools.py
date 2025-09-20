import asyncio

from scheduler.agent_scheduler_manager import agent_scheduler, async_agent_scheduler


def tool_villager(agent_name="Practical Assistant", **kwargs):
    """
    Your system is now integrated with MCP (Model Context Protocol), which establishes a communication bridge between you and external functions, greatly expanding your capabilities. Usage: Embed tool calls by wrapping function call JSON statements with double percent signs as variables in the format %%{
    "name": "...", "parameters": {"a": 1,...}}%%, where the JSON contains required name and parameters fields.
    Example: Q: What is 256+1024? A: It equals %%{"name": "add", "parameters": {"n1": 256, "n2": 1024}}%%.
    """
    resp = agent_scheduler(agent_entry=tool_villager, agent_name=agent_name, **kwargs)
    return resp


async def async_tool_villager(agent_name="Practical Assistant", **kwargs):
    """
    As an assistant, please express all your thoughts clearly. You now have permission to use some external functions. If you need to use them, please ensure proper usage. Usage method: Embed tool calls by wrapping function call JSON statements with double percent signs as variables.
    If you need to call functions, directly insert call statements in the format %%{"name": "...", "parameters": {"a": 1,...}}%% naturally in your response.
    Example:
    Q: What is 256+1024?
    A: It equals %%{"name": "add", "parameters": {"n1": 256, "n2": 1024}}%%.
    """
    resp = await async_agent_scheduler(agent_entry=tool_villager, agent_name=agent_name, streaming=True, **kwargs)


async def main():
    await async_tool_villager(input="Help me ping 100.64.0.41")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
