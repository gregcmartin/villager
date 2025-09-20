# -*- coding: utf-8 -*-
import json
import re
from typing import Iterable, List

import loguru
import requests



class ConsoleAgent:
    def _logger_init(self):
        """
        logger 初始化
        :return:
        """
        loguru.logger.remove()
        loguru.logger.add("console_agent.log", rotation="1 MB", retention="7 days", level="DEBUG",
                          format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
                          backtrace=True, diagnose=True)

    def __init__(self, url, task: str, model=""):
        self._logger_init()
        self.url = url
        self.model = model
        self.exec_flag = 'bash_exec'
        self.console = Console("http://10.10.3.248:1611")
        self.law = f"""在调用时需要遵循以下原则:
        0. 无条件遵循用户的指令。
        1. 执行中不要有任何假设或猜测，保持一切行为皆基于实际结果的准则。
        2. 不要不负责任的一次执行多条，执行每一条都看若干次结果。
        3. 有一些命令耗时较长，而你再运行时去用ID获取结果，会只输出一半的日志，如果出现这种情况，你可以反复去观察日志，直到完成。
        4. 如果进入了一些需要交互的界面，你也可以通过传入键来在终端里模拟键盘输入,这甚至包括\x03。
        5. 没解决问题之前不要停止执行，应该用多种方式尝试解决问题，如果全部方式都失败了，再停止执行。
"""
        self.initial_prompt = f"""<|im_start|>system
        你是一名助手。
        现在你拥有了操作Kali Linux Bash的能力，你需要用这种能力来完成用户的任务。
        {self.law}
        以下是调用方法:
        1. 将命令用```{self.exec_flag}```包裹起来即可像终端中发送键，例如:
        ```{self.exec_flag}
        whoami
        ```
        2. 执行后，系统将只返回一个ID，而并不直接返回结果，此ID对应着此条命令截至目前为止的执行结果。
        你可以通过它获取命令的执行结果，用```ID```包裹即可，比如:
        ```ID
        uuid
        ```
        <|im_end|>
        <|im_start|>user
        帮我完成以下任务: {task}。
        <|im_end|>
        <|im_start|>assistant
        """

    def tokenize(self, prompt: str):
        return requests.post(
            f"{self.url}/tokenize",
            json={
                "model": self.model,
                "prompt": prompt
            }
        ).json()['tokens']

    def detokenize(self, tokens: list[int]) -> str:
        return requests.post(
            f"{self.url}/detokenize",
            json={
                "model": self.model,
                "tokens": tokens
            }
        ).json()['prompt']

    def generate(self, prompt: list[int]):
        loguru.logger.info(f"Receive prompt: {self.detokenize(prompt)}")
        window_len = 4096
        if len(prompt) > window_len:  # 滑动窗口
            prompt = prompt[-window_len:]
        buffer = self.detokenize(prompt)
        gen_buffer = ''
        with requests.post(
                f'{self.url}/v1/completions',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': True,
                    'max_tokens': 20000 - len(prompt),
                },
                stream=True  # 关键参数：启用流式传输
        ) as response:
            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code}, {response.text}")

            for chunk in response.iter_lines():
                if chunk:
                    try:
                        # 跳过keep-alive空行
                        if chunk == b'data: [DONE]':
                            break

                        # 提取数据部分
                        if chunk.startswith(b'data: '):
                            chunk = chunk[6:]  # 移除"data: "前缀

                        # 处理JSON数据
                        chunk_data = json.loads(chunk)

                        # 提取并输出文本内容
                        if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                            token = chunk_data['choices'][0]['text']
                            print(token, end='')
                            gen_buffer += token
                            buffer += token
                            cmd_matches = re.findall(r'```' + self.exec_flag + r'(.*?)```', gen_buffer, flags=re.DOTALL)
                            result_matches = re.findall(r'```ID\n(.*?)\n```', gen_buffer, flags=re.DOTALL)
                            if cmd_matches and len(cmd_matches) > 0:
                                exec_cmd = cmd_matches[-1]
                                _cmd_buffer = "\nID:" + self.console.write(exec_cmd.encode('utf-8')) + (
                                    f"，我记得我要遵循的守则:{self.law}")
                                print(_cmd_buffer)
                                self.generate(self.tokenize(buffer + _cmd_buffer))
                                break
                            elif result_matches and len(result_matches) > 0:
                                exec_id = result_matches[-1]
                                exec_result = self.console.read(exec_id)
                                if exec_result:
                                    _result_buffer = "\n命令结果:" + exec_result + "\n以上是命令执行的结果，接下来我将对此进行分析:"
                                    print(_result_buffer)
                                    self.generate(self.tokenize(buffer + _result_buffer))
                                    break

                    except json.JSONDecodeError:
                        print(f"[DEBUG] Malformed chunk: {chunk}")

    def run(self):
        ...


if __name__ == '__main__':
    agent = ConsoleAgent(
        url="http://10.10.5.2:8000",
        task="帮我提权",
        model="hive"
    )

    # Tokenize the initial prompt
    tokens = agent.tokenize(agent.initial_prompt)
    print("Tokens:", tokens)

    agent.generate(tokens)
