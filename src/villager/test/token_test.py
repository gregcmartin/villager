# ****************************************************************************
# 尝试使用Langchain API调用LLM进行prefill
# ****************************************************************************
from kink import di
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import Master

if __name__ == '__main__':
    model = di['llm']
    output_parser = StrOutputParser()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("assistant", "{input}"),
        ("user", "Continuously continue")
    ])
    chain = prompt | model | output_parser
    res = chain.invoke({"input": """我可以帮助尝试运行 `ping` 命令以获取相关信息。如果失败，可能仍受到权限限制。开始尝试执行命令：

('\n正在 Ping 100.64.0.41 具有 32 字节的数据:\n来自 100.64.0.41 的回复: 字节=32 时间=392ms TTL=64\n来自 100.64.0.41 的回复: 字节=32 时间=93ms TTL=64\n来自 100.64.0.41 的回复: 字节=32 时间=90ms TTL=64\n来自 100.64.0.41 的回复: 字节=32 时间=101ms TTL=64\n\n100.64.0.41 的 Ping 统计信息:\n    数据包: 已发送 = 4，已接收 = 4，丢失 = 0 (0% 丢失)，\n往返行程的估计时间(以毫秒为单位):\n    最短 = 90ms，最长 = 392ms，平均 = 169ms\n', '', 0)
"""})
    print(res)
