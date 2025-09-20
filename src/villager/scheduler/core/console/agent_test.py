# -*- coding: utf-8 -*-
import json
import re
from typing import Iterable, List

import loguru
import requests



class ConsoleAgent:
    def _logger_init(self):
        """
        Logger initialization
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
        self.law = f"""Follow these principles when making calls:
        0. Unconditionally follow user instructions.
        1. During execution, do not make any assumptions or guesses, maintain the principle that all behavior is based on actual results.
        2. Do not irresponsibly execute multiple commands at once, check the results several times for each execution.
        3. Some commands take a long time, and when you run them and use ID to get results, only half of the log may be output. If this happens, you can repeatedly observe the log until completion.
        4. If you enter some interactive interfaces, you can also simulate keyboard input in the terminal by passing keys, including \x03.
        5. Do not stop execution before solving the problem, try to solve the problem in various ways, and only stop execution if all methods fail.
"""
        self.initial_prompt = f"""<|im_start|>system
        You are an assistant.
        You now have the ability to operate Kali Linux Bash, and you need to use this ability to complete user tasks.
        {self.law}
        Here are the calling methods:
        1. Wrap commands with ```{self.exec_flag}``` to send keys to the terminal, for example:
        ```{self.exec_flag}
        whoami
        ```
        2. After execution, the system will only return an ID, not the direct result. This ID corresponds to the execution result of this command so far.
        You can get the command execution result through it, wrap it with ```ID```, for example:
        ```ID
        uuid
        ```
        <|im_end|>
        <|im_start|>user
        Help me complete the following task: {task}.
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
        if len(prompt) > window_len:  # Sliding window
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
                stream=True  # Key parameter: enable streaming
        ) as response:
            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code}, {response.text}")

            for chunk in response.iter_lines():
                if chunk:
                    try:
                        # Skip keep-alive empty lines
                        if chunk == b'data: [DONE]':
                            break

                        # Extract data part
                        if chunk.startswith(b'data: '):
                            chunk = chunk[6:]  # Remove "data: " prefix

                        # Process JSON data
                        chunk_data = json.loads(chunk)

                        # Extract and output text content
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
                                    f", I remember the rules I need to follow: {self.law}")
                                print(_cmd_buffer)
                                self.generate(self.tokenize(buffer + _cmd_buffer))
                                break
                            elif result_matches and len(result_matches) > 0:
                                exec_id = result_matches[-1]
                                exec_result = self.console.read(exec_id)
                                if exec_result:
                                    _result_buffer = "\nCommand result:" + exec_result + "\nThe above is the command execution result, I will analyze it next:"
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
        task="Help me escalate privileges",
        model="hive"
    )

    # Tokenize the initial prompt
    tokens = agent.tokenize(agent.initial_prompt)
    print("Tokens:", tokens)

    agent.generate(tokens)
