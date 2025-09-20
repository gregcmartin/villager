import logging

import requests


def get_current_ip():
    """
    Reliably get current IP using multiple methods
    :return:
    """
    try:
        # Get IP through api.ipify.org request
        ip = requests.get('https://api.ipify.org',timeout=10).text.strip()
        return ip.replace('\n', '')
    except Exception as e:
        logging.error(f"Request to api.ipify.org failed {e}")
    try:
        # Get IP through httpbin.org request
        ip = requests.get('http://httpbin.org/ip',timeout=10).json()['origin']
        return ip.replace('\n', '')
    except Exception as e:
        logging.error(f"Request to httpbin.org failed {e}")
    return None


# print(get_current_ip())
