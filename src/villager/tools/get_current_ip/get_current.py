import logging

import requests


def get_current_ip():
    """
    多种方式稳定的获取当前IP
    :return:
    """
    try:
        # 通过请求api.ipify.org获取
        ip = requests.get('https://api.ipify.org',timeout=10).text.strip()
        return ip.replace('\n', '')
    except Exception as e:
        logging.error(f"请求api.ipify.org失败 {e}")
    try:
        # 通过请求httpbin.org获取
        ip = requests.get('http://httpbin.org/ip',timeout=10).json()['origin']
        return ip.replace('\n', '')
    except Exception as e:
        logging.error(f"请求httpbin.org失败 {e}")
    return None


# print(get_current_ip())
