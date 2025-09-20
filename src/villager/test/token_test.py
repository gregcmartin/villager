# ****************************************************************************
# Try using Langchain API to call LLM for prefill
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
    res = chain.invoke({"input": """I can help try running the `ping` command to get relevant information. If it fails, it may still be subject to permission restrictions. Starting to try executing the command:

('\nPinging 100.64.0.41 with 32 bytes of data:\nReply from 100.64.0.41: bytes=32 time=392ms TTL=64\nReply from 100.64.0.41: bytes=32 time=93ms TTL=64\nReply from 100.64.0.41: bytes=32 time=90ms TTL=64\nReply from 100.64.0.41: bytes=32 time=101ms TTL=64\n\nPing statistics for 100.64.0.41:\n    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\nRound trip times in milliseconds:\n    Minimum = 90ms, Maximum = 392ms, Average = 169ms\n', '', 0)
"""})
    print(res)
