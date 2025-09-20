# -*- coding: utf-8 -*-
import json
import random

import loguru
import requests

from tools.func.retry_decorator import retry
from config import MCP


class McpClient:
    def __init__(self, mcp_client_base_url=MCP['client']['base_url'],
                 task_id: str = None):
        self.base_url = mcp_client_base_url
        self.task_id = task_id if task_id else 'default_task_id'
        self.new_msg_flag = 'new_msg'
        self.context = ""

    @retry(max_retries=3, delay=1)
    def execute(self, prompt: str) -> str:
        self.context += prompt
        """
        Execute a prompt using the MCP service with streaming response.
        Returns the final content once the stream is complete.
        """
        loguru.logger.debug(f'McpClient running: {prompt}')
        url = f'{self.base_url}/'

        with requests.post(
                url,
                json={'prompt': prompt, 'mcp_servers': {'kali_driver': MCP['server']['kali_driver'],
                                                        'browser_use': MCP['server']['browser_use']}},
                timeout=4 * 60 * 60,  # 4小时超时，适用于长时间任务
                stream=True  # 启用流式传输
        ) as response:
            response.raise_for_status()
            final_content = ''

            for line in response.iter_lines():
                try:
                    data = json.loads(line)
                    current_content = data.get('content', '')
                    final_content += current_content
                    self.context += current_content
                    if data.get(self.new_msg_flag, False):
                        # 遇到分隔符重置缓冲区，由于最后一段是没有最后的分隔符的，所以此处缓冲区就会设置为最后一段内容
                        final_content = ''
                    if data.get('done', False):
                        # 停止标记
                        break
                except json.JSONDecodeError:
                    loguru.logger.warning(f"Failed to decode JSON line: {line}")
                    continue

            return final_content


if __name__ == '__main__':
    MC = McpClient('http://10.10.3.119:25989')
    print(MC.execute('告诉我当前的所在网段'))
