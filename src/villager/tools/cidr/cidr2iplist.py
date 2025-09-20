import ipaddress


def cidr_to_ip_list(cidr):
    """
    将 CIDR 范围转换为 IP 地址列表
    :param cidr: str, 例如 '0.0.0.0/24'
    :return: list, 包含所有 IP 地址的字符串列表
    """
    try:
        network = ipaddress.ip_network(cidr)
        return [str(ip) for ip in network.hosts()]
    except ValueError as e:
        raise ValueError(f"无效的CIDR格式: {cidr}，错误: {e}")
