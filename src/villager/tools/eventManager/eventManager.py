import logging
from datetime import datetime

import diamond_shovel.tools.dingtalk.sender


class EventManager:
    def __init__(self):
        self.handlers = {
            "advisory": self.send_advisory,
            "normal": self.send_normal,
            "serious": self.send_serious,
            "critical": self.send_critical
        }
        self.dtkLog = diamond_shovel.tools.dingtalk.sender.Manager()

    def submit(self, message, level, submessage="影响范围未知"):
        """ Submit an event with a specific severity level. """
        handler = self.handlers.get(level)
        try:
            if handler:
                handler(
                    f"发生事件 等级: {level} 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n原日志:{message}\n标注:{submessage}")

            else:
                logging.error(f"不知道的等级: {level}")
        except Exception as e:
            logging.error("事件注册器发生错误")
            logging.error(e)

    def send_advisory(self, message):
        """ Handle advisory level events. """
        self.dtkLog.info(message)

    def send_normal(self, message):
        """ Handle normal level events. """
        self.dtkLog.info(message)

    def send_serious(self, message):
        """ Handle serious level events. """
        self.dtkLog.warn(message)

    def send_critical(self, message):
        """ Handle disastrous level events. """
        self.dtkLog.warn2(message)
