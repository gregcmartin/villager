import base64
import configparser
import hashlib
import hmac
import json
import threading
import time

import requests
from kink import inject


class Manager:
    @inject
    def __init__(self, config: configparser.ConfigParser):
        self.secret = config.get('dingtalk', 'bot_key')
        self.webhook = config.get('dingtalk', 'api_url') + "/robot/send?access_token=" + config.get('dingtalk', 'access_token')

    def send_dtk_msg(self, message):
        """
        从config.py中读取配置
        在反馈群中调用机器人发送信息
        :param message:
        :return:
        """
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f'{timestamp}\n{self.secret}'
        hmac_code = hmac.new(self.secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()
        signature = base64.b64encode(hmac_code).decode('utf-8')
        signed_url = f'{self.webhook}&timestamp={timestamp}&sign={signature}'
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        data = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        response = requests.post(signed_url, headers=headers, data=json.dumps(data))
        print(response.text)

    def send_message_in_thread(self, message):
        """
        非阻塞运行的发送信息机器人
        功能同send_dingtalk_message
        """
        try:
            thread = threading.Thread(target=self.send_dtk_msg, args=(message,))
            thread.start()
        except Exception as e:
            print(f"发送信息失败: {e}")

    def info(self, message):
        thread = threading.Thread(target=self.send_dtk_msg, args=(f"[信息] {message}",))
        thread.start()

    def warn(self, message):
        thread = threading.Thread(target=self.send_dtk_msg, args=(f"[警告] {message}",))
        thread.start()

    def warn2(self, message):
        thread = threading.Thread(target=self.send_dtk_msg, args=(f"[严重警告] {message}",))
        thread.start()
