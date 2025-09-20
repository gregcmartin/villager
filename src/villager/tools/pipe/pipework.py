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
    # Place original business logic code here
    return f"Response: {message}"

    if __name__ == '__main__':
        # Use pipeline style call
        result = Pipe("Please ping www.baidu.com for me") | chat_with_tool_villager
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
