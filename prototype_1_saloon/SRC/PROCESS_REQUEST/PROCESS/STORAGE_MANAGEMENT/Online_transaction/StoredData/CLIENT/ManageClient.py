
import json
from pathlib import Path
import os

def writeout_data(seq_key, session_key, phone_number, request_data, action):
    # Write to file
    try:
        if action == "CREATE-CLIENT":
            f_path = "{0}\\StoreData\\{1}#{2}#{3}.json".format(Path(__file__).parent, seq_key, phone_number, session_key)
        elif action == "UPDATE-CLIENT":
            f_path = "{0}\\HistoryData\\{1}#{2}#{3}.json".format(Path(__file__).parent, seq_key, phone_number, session_key)
        with open(f_path, "w+") as f:
            json.dump(request_data, f, indent=4)  # indent=4 makes it pretty-printed
            return {"result" : "record subimmited", "err_msg" : None}
    except Exception as e:
        return {"result" : "record subimmited", "err_msg" : e}

def delete_data(seq_key, session_key, phone_number):
    try:
        f_path = "{0}\\StoreData\\{1}#{2}#{3}.json".format(Path(__file__).parent, seq_key, phone_number, session_key)
        if os.path.exists(f_path):
            os.remove(f_path)
        return {"result" : "record deleted", "err_msg" : None}
    except Exception as e:
        return {"result" : "record deleted", "err_msg" : e}

def update_client_meta_data(meta_data, seq_id, phone_number):
    meta_data[seq_id] = phone_number
    return meta_data

