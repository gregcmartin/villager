import loguru
from kink import inject, di
import requests


class checkEnv:
    def __init__(self, min_memory=256, need_camera=False):
        self.min_memory = min_memory
        self.need_camera = need_camera
        try:
            loguru.logger.warning("Starting environment check")
            loguru.logger.debug('-' * 32)
            self.checkCamera()
            self.checkMemory()
            self.checkNetwork()
            loguru.logger.debug('-' * 32)
            loguru.logger.success("Environment check passed")
        except Exception as e:
            loguru.logger.debug('-' * 32)
            loguru.logger.error("Environment check failed")
            exit(0)

    @inject
    def checkNetwork(self, proxy: str):
        """
        Check if the network environment is normal, supports proxy.

        :param proxy: Proxy server URL
        :return: Whether the network environment is normal
        """
        # First check DNS, see if we can resolve Baidu address
        import socket
        try:
            ip = socket.gethostbyname("www.baidu.com")
            loguru.logger.info(f"DNS: www.baidu.com -> {ip}")
        except Exception as e:
            loguru.logger.error("DNS resolution failed, please check network environment")
            raise Exception("DNS resolution failed, please check network environment")
        loguru.logger.success("DNS normal")

        try:
            requests.get("http://www.baidu.com")
            loguru.logger.success("Domestic internet connection normal")
        except Exception as e:
            raise Exception("Actual network environment test abnormal")
        try:
            if proxy:
                loguru.logger.info('Using proxy')
                cn_res = requests.get("http://www.baidu.com", proxies={"http": proxy, "https": proxy})
                loguru.logger.success("Domestic internet proxy connection normal")
                if len(cn_res.content) < 1:
                    loguru.logger.error(f"Domestic internet proxy connection abnormal length:{len(cn_res.content)}")
                    raise Exception("Domestic internet proxy connection abnormal")
                res = requests.get("http://www.google.com", proxies={"http": proxy, "https": proxy})
                if len(res.content) < 1:
                    loguru.logger.error(f"International internet proxy connection abnormal length:{len(res.content)}")
                    raise Exception("International internet proxy connection abnormal")
                loguru.logger.success(f"International internet proxy connection normal length:{len(res.content)}")
        except Exception as e:
            loguru.logger.error("Network environment proxy test abnormal")
            raise Exception("Actual network environment proxy test abnormal")
        # Get network interface information
        import psutil
        net = psutil.net_if_addrs()
        for k, v in net.items():
            for item in v:
                if item.family == 2:
                    loguru.logger.info(f"Network: {k} {item.address}")
                    break
        loguru.logger.success("Network environment normal")

    def checkCamera(self):
        if self.need_camera:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                loguru.logger.error("Camera cannot be opened")
                raise Exception("Camera cannot be opened")
            # Get camera resolution and total number of cameras
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            # Get total number of cameras in the system
            count = 0
            while True:
                test_cap = cv2.VideoCapture(count)
                if not test_cap.isOpened():
                    break
                test_cap.release()
                count += 1
            loguru.logger.info(f"Camera: {width}x{height}, {count} cameras")
            # Take a picture
            loguru.logger.info("Testing camera...")
            ret, frame = cap.read()
            if not ret or frame is None:
                loguru.logger.error("Camera cannot capture image")
                raise Exception("Camera cannot capture image")
            loguru.logger.success("Camera normal")
            cap.release()  # Release camera

    def checkMemory(self):
        import psutil
        memory = psutil.virtual_memory().total / 1024 / 1024
        current_used_memory = psutil.virtual_memory().used / 1024 / 1024
        if memory-current_used_memory < self.min_memory:
            loguru.logger.error(f"Insufficient memory {self.min_memory}MB, current available memory {memory - current_used_memory}MB")
            raise Exception("Insufficient memory")
        used_rate = current_used_memory / memory * 100
        loguru.logger.info(f"Memory: {current_used_memory}/{memory}MB {used_rate}%")
        loguru.logger.success("Memory normal")


if __name__ == '__main__':
    di["proxy"] = "https://huancun:ylq123..@home.hc26.org:5422"
    checkEnv(need_camera=True, min_memory=256)
