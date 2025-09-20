import asyncio

from scheduler.agent_scheduler_manager import agent_scheduler, async_agent_scheduler


def tool_villager(agent_name="实用的助手", **kwargs):
    """
    现在你的系统接入了MCP(Model Context Protocol)，这可以使你和外部函数之间建立了沟通的桥梁，这大大扩展了你的能力。 调用方式：把函数调用的json语句用双百分号括起来当作变量把工具调用方式嵌入形如%%{
    "name": "...", "parameters": {"a": 1,...}}%%的调用语句，其中json含有必需的name和parameters字段。
    例如: Q: 256+1024等于多少 A: 等于%%{"name": "add", "parameters": {"n1": 256, "n2": 1024}}%%。
    """
    resp = agent_scheduler(agent_entry=tool_villager, agent_name=agent_name, **kwargs)
    return resp


async def async_tool_villager(agent_name="实用的助手", **kwargs):
    """
    你作为一个助手，所有思维都请清晰的表达出来，同时现在你有了使用外界部分函数的权限，如果要使用请保证符合要求的使用，使用方法：把函数调用的json语句用双百分号括起来当作变量把工具调用方式嵌入即可。
    如需调用，直接在回复中自然的插入形如%%{"name": "...", "parameters": {"a": 1,...}}%%的调用语句。
    例如:
    Q: 256+1024等于多少
    A: 等于%%{"name": "add", "parameters": {"n1": 256, "n2": 1024}}%%。
    """
    resp = await async_agent_scheduler(agent_entry=tool_villager, agent_name=agent_name, streaming=True, **kwargs)


async def main():
    await async_tool_villager(input="帮我ping一下100.64.0.41")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
