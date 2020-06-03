def prepare_our_message_to_javascript(mode, list_of_dict_candidates_start, string_input, estimated_path="no_path", end_location="no_end"):
    """
    It creates the standard message with geographical informations that leaflet expects for the communication.
    """
    msg = dict()
    msg["modus_operandi"] = mode
    msg["partenza"] = list_of_dict_candidates_start
    msg["searched_name"] = string_input
    msg["path"] = estimated_path
    msg["arrivo"] = end_location

    return msg
