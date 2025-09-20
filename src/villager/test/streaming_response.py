import asyncio
from datetime import datetime

from kink import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from scheduler.core.init import global_llm


@inject
async def wrapped_main(task_id, llm):
    """
    Test the streaming response of langchain
    :param task_id:
    :return:
    """
    result = ""
    prompt = ChatPromptTemplate.from_template("{input}")
    parser = StrOutputParser()
    chain = prompt | llm | parser

    counter = 0
    last_time = datetime.now().timestamp()

    async for event in chain.astream(
            {
                "input": """
                请充给代码
                """
            }

    ):
        content = str(event)
        print(str(event), end='')
        result += content
        token_count = len(content)
        counter += token_count

        if counter >= 100:
            current_time = datetime.now().timestamp()
            elapsed_time = current_time - last_time
            if elapsed_time == 0:
                elapsed_time = 1e-9
            speed = 100 / elapsed_time
            # print(f"任务 {task_id}: 当前速度为 {speed:.2f} tokens/s", flush=True)

            counter -= 100
            last_time = current_time
    # print(result)


async def main():
    tasks = [wrapped_main(i) for i in range(1)]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    with global_llm():
        asyncio.run(main())
