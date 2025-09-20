import loguru
from kink import inject, di
import requests


class checkEnv:
    def __init__(self, min_memory=256, need_camera=False):
        self.min_memory = min_memory
        self.need_camera = need_camera
        try:
            loguru.logger.warning("开始环境检查")
            loguru.logger.debug('-' * 32)
            self.checkCamera()
            self.checkMemory()
            self.checkNetwork()
            loguru.logger.debug('-' * 32)
            loguru.logger.success("环境检查通过")
        except Exception as e:
            loguru.logger.debug('-' * 32)
            loguru.logger.error("环境检查失败")
            exit(0)

    @inject
    def checkNetwork(self, proxy: str):
        """
        检查网络环境是否正常，支持代理。

        :param proxy: 代理服务器的 URL
        :return: 网络环境是否正常
        """
        # 先检查一下dns，看能不能解析百度地址
        import socket
        try:
            ip = socket.gethostbyname("www.baidu.com")
            loguru.logger.info(f"DNS: www.baidu.com -> {ip}")
        except Exception as e:
            loguru.logger.error("DNS解析失败，请检查网络环境")
            raise Exception("DNS解析失败，请检查网络环境")
        loguru.logger.success("DNS正常")

        try:
            requests.get("http://www.baidu.com")
            loguru.logger.success("通联国内互联网正常")
        except Exception as e:
            raise Exception("实际通联网络环境测试异常")
        try:
            if proxy:
                loguru.logger.info('使用代理')
                cn_res = requests.get("http://www.baidu.com", proxies={"http": proxy, "https": proxy})
                loguru.logger.success("通联国内互联网代理正常")
                if len(cn_res.content) < 1:
                    loguru.logger.error(f"通联国内互联网代理异常 length:{len(cn_res.content)}")
                    raise Exception("通联国内互联网代理异常")
                res = requests.get("http://www.google.com", proxies={"http": proxy, "https": proxy})
                if len(res.content) < 1:
                    loguru.logger.error(f"通联国外互联网代理异常 length:{len(res.content)}")
                    raise Exception("通联国外互联网代理异常")
                loguru.logger.success(f"通联国外互联网代理正常 length:{len(res.content)}")
        except Exception as e:
            loguru.logger.error("通联网络环境代理测试异常")
            raise Exception("实际通联网络环境代理测试异常")
        # 获取网卡信息
        import psutil
        net = psutil.net_if_addrs()
        for k, v in net.items():
            for item in v:
                if item.family == 2:
                    loguru.logger.info(f"Network: {k} {item.address}")
                    break
        loguru.logger.success("网络环境正常")

    def checkCamera(self):
        if self.need_camera:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                loguru.logger.error("摄像头无法打开")
                raise Exception("摄像头无法打开")
            # 获取摄像头的分辨率和总共的摄像头数量
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            # 获取系统中摄像头的总数量
            count = 0
            while True:
                test_cap = cv2.VideoCapture(count)
                if not test_cap.isOpened():
                    break
                test_cap.release()
                count += 1
            loguru.logger.info(f"Camera: {width}x{height}, {count} cameras")
            # 拍摄一张图片
            loguru.logger.info("正在测试摄像头...")
            ret, frame = cap.read()
            if not ret or frame is None:
                loguru.logger.error("摄像头无法拍摄图片")
                raise Exception("摄像头无法拍摄图片")
            loguru.logger.success("摄像头正常")
            cap.release()  # 释放摄像头

    def checkMemory(self):
        import psutil
        memory = psutil.virtual_memory().total / 1024 / 1024
        current_used_memory = psutil.virtual_memory().used / 1024 / 1024
        if memory-current_used_memory < self.min_memory:
            loguru.logger.error(f"内存不足{self.min_memory}MB，当前剩余内存{memory - current_used_memory}MB")
            raise Exception("内存不足")
        used_rate = current_used_memory / memory * 100
        loguru.logger.info(f"Memory: {current_used_memory}/{memory}MB {used_rate}%")
        loguru.logger.success("内存正常")


if __name__ == '__main__':
    di["proxy"] = "https://huancun:ylq123..@home.hc26.org:5422"
    checkEnv(need_camera=True, min_memory=256)
