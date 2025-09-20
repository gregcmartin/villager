def format_anchor_message(anchors):
    """
    Anchor offline text formatting function
    :param anchors:
    :return:
    """
    if anchors:
        message_lines = [f"Anchor {anchor.id} - {anchor.location} offline" for anchor in anchors]
        return "\n".join(message_lines)
    else:
        return "Currently no offline anchors."

# List deduplication function
def list_unique(input_list):
    """
    List deduplication function
    :param input_list:
    :return:
    """
    return list(set(input_list))
