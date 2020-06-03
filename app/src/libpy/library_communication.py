def prepare_our_message_to_javascript(mode,  string_input, start_location, estimated_path="no_path", end_location="no_end"):
    """
    It creates the standard message with geographical informations that leaflet expects for the communication.
    """
    # leaflet vuole le coordinate invertite (x e y). Per le path lo facciamo già in calculate_path
    for start in start_location:
        xy =start['coordinate'][:]
        start['coordinate'][0]=xy[1]
        start['coordinate'][1]=xy[0]
    if end_location is not "no_end":
        for end in end_location:
            xy =end['coordinate'][:]
            end['coordinate'][0]=xy[1]
            end['coordinate'][1]=xy[0]

    msg = dict()
    msg["modus_operandi"] = mode
    msg["partenza"] = start_location
    msg["searched_name"] = string_input
    msg["path"] = estimated_path
    msg["arrivo"] = end_location

    return msg
