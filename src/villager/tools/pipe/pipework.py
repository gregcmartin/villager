class PipeFunction:
    def __init__(self, func):
        self.func = func

    def __ror__(self, other):
        return self.func(other)


def pipeable(func):
    return PipeFunction(func)


class Pipe:
    """
    def chat_with_tool_villager(message: str) -> str:
    # 这里放置原来的业务逻辑代码
    return f"响应: {message}"

    if __name__ == '__main__':
        # 使用管道风格调用
        result = Pipe("给我ping一下www.baidu.com") | chat_with_tool_villager
        print(result.invoke())
    """
    def __init__(self, value):
        self.value = value

    def __or__(self, func):
        return Pipe(func(self.value))

    def invoke(self):
        return self.value

    def __repr__(self):
        return repr(self.value)
