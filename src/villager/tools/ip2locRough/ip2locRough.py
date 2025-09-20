import logging

import requests
from geopy.distance import geodesic


def get_geo_from_ip(ip):
    for i in range(5):
        try:
            url = f'http://ip-api.com/json/{ip}'
            response = requests.get(url,timeout=30)
            data = response.json()
            if response.status_code == 200 and data['status'] == 'success':
                return {'latitude': data['lat'], 'longitude': data['lon']}
            else:
                logging.error(f"获取IP地址{ip}的地理位置失败，错误信息: {data}")
        except Exception as e:
            logging.error(f"获取IP地址{ip}的地理位置失败，错误信息: {e}")
    return None


def judg_rough_ip2loc_dist(ip, latitude, longitude):
    # 从IP获取地理位置
    ip_geo = get_geo_from_ip(ip)
    ip_latitude = ip_geo['latitude']
    ip_longitude = ip_geo['longitude']

    # 计算距离
    user_loc = (latitude, longitude)
    ip_loc = (ip_latitude, ip_longitude)
    distance = geodesic(user_loc, ip_loc).kilometers
    return distance
