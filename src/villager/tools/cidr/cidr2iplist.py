import ipaddress


def cidr_to_ip_list(cidr):
    """
    Convert CIDR range to IP address list
    :param cidr: str, for example '0.0.0.0/24'
    :return: list, containing all IP address strings
    """
    try:
        network = ipaddress.ip_network(cidr)
        return [str(ip) for ip in network.hosts()]
    except ValueError as e:
        raise ValueError(f"Invalid CIDR format: {cidr}, error: {e}")
