class McpConsole:
    def __init__(self,base_url: str = "http://10.10.3.119:1612"):
        self.base_url = base_url
    def get_terminal(self):
        return