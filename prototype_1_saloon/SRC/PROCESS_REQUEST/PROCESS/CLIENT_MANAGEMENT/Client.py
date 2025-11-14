import os
import json

def update_system_fields(data, prev_session_key, current_session_number):
    if "versionNo" in data["barber_shop"]:
        data["barber_shop"]["versionNo"] = data["barber_shop"]["versionNo"] + 1
        data["barber_shop"]["prev_idx"] = prev_session_key
        data["barber_shop"]["current_idx"] = current_session_number
    else:
        data["barber_shop"]["versionNo"] = 1
        data["barber_shop"]["prev_idx"] = prev_session_key
        data["barber_shop"]["current_idx"] = current_session_number
    return data

def current_sys_fields(phone_number, client_meta_data_common):
        current_file = os.path.abspath(__file__)
        parent_folder = os.path.dirname(current_file)
        grand_parent_folder = os.path.dirname(parent_folder)
        file_path = "{}/STORAGE_MANAGEMENT/Online_transaction/StoredData/CLIENT/meta-data/client_meta_data.json".format(grand_parent_folder)
        if os.path.exists(file_path):
            with open(file_path, "r") as f_ptr:
                client_meta_file = f_ptr.read()
                if client_meta_file:
                    client_meta_file = json.loads(client_meta_file)
                    client_seq_id = client_meta_file["clients"][phone_number]["client_id"]
                    session_id = client_meta_file["clients"][phone_number]["session_id"]
                    return client_seq_id, session_id
        else:
            if client_meta_data_common:
                client_seq_id = client_meta_data_common["clients"][phone_number]["client_id"]
                session_id = client_meta_data_common["clients"][phone_number]["session_id"]
                return client_seq_id, session_id   
        return None, None

def load_record(record_version, phone_number, client_seq_id = None, session_id = None, request_data = {}, current_data = {}, combined_paths = {}):
    if record_version == "CURRENT":
        current_file = os.path.abspath(__file__)
        parent_folder = os.path.dirname(current_file)
        grand_parent_folder = os.path.dirname(parent_folder)
        if phone_number and client_seq_id and session_id:
            file_path = "{}/STORAGE_MANAGEMENT/Online_transaction/StoredData/CLIENT/StoreData/{}#{}#{}.json".format(
                grand_parent_folder, client_seq_id, phone_number, session_id
            )
            if os.path.exists(file_path):
                with open(file_path, "r") as f_ptr:
                    client_record = f_ptr.read()
                    return json.loads(client_record), None
            else:
                return None, "RECORD-NOT-FOUND"
    elif record_version == "NEW":
        merged_data, err_msg = merge_record(request_data, current_data, combined_paths)
        return merged_data, None
    else:
        return None, "RECORD-VERSION-MISSING"
    return {}, "RECORD-NOT-FOUND"

def validate_fields(requst_data, end_paths):
    missing_fields = []
    if "modifyFields" in requst_data:
        for each_field in requst_data["modifyFields"]:
            if each_field not in end_paths:
                missing_fields.append(each_field)
        return {"missingFields" : missing_fields, "errMsg" : ""}
    return {"missingFields" : missing_fields, "errMsg" : "field modification not found"}

def update_by_key(data, target_key, new_value):
    for key, value in data.items():

        # Found the key → update then return whole dict
        if key == target_key:
            data[key] = new_value
            return data

        # Search deeper only in nested dictionaries
        if isinstance(value, dict):
            result = update_by_key(value, target_key, new_value)
            if result is not None:       # means update happened
                return data

    return None  # Not found in this branch



def merge_record(requst_data, loaded_data, combined_paths):
    for each_field in requst_data["modifyFields"]:
        path = combined_paths["path"][each_field]
        new_value = requst_data["modifyFields"][each_field]
        updated_data = update_by_key(loaded_data, path.split(".")[-1], new_value)
        if updated_data:
            loaded_data = updated_data
    return loaded_data, ""

def get_keys_paths(schema, parent_path=""):
    paths = []
    if isinstance(schema, str):
        return schema
    for k, v in schema.items():
        path = f"{parent_path}.{k}" if parent_path else k
        if isinstance(v, dict):
            paths.append(get_keys_paths(v, path, True))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    paths.append(get_keys_paths(item, f"{path}[{i}]", True))
        else:
            return path
    return paths
