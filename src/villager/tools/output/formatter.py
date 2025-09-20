def format_anchor_message(anchors):
    """
    锚点离线文字的格式化函数
    :param anchors:
    :return:
    """
    if anchors:
        message_lines = [f"锚点 {anchor.id} - {anchor.location} 离线" for anchor in anchors]
        return "\n".join(message_lines)
    else:
        return "当前无离线锚点。"

# list去重函数
def list_unique(input_list):
    """
    列表去重函数
    :param input_list:
    :return:
    """
    return list(set(input_list))