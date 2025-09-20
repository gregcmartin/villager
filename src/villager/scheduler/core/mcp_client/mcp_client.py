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
                timeout=4 * 60 * 60,  # 4 hour timeout, suitable for long-running tasks
                stream=True  # Enable streaming
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
                        # Reset buffer when encountering separator, since the last segment has no final separator, the buffer will be set to the last segment content
                        final_content = ''
                    if data.get('done', False):
                        # Stop marker
                        break
                except json.JSONDecodeError:
                    loguru.logger.warning(f"Failed to decode JSON line: {line}")
                    continue

            return final_content


if __name__ == '__main__':
    MC = McpClient('http://10.10.3.119:25989')
    print(MC.execute('Tell me the current network segment'))
