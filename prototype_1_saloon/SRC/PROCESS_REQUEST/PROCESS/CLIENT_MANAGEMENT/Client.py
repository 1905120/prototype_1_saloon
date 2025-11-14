import os
import json

def update_system_fields(data, new_session_number, client_id):
    if "versionNo" in data["barber_shop"]:
        data["barber_shop"]["versionNo"] = data["barber_shop"]["versionNo"] + 1
    else:
        data["barber_shop"]["versionNo"] = 1
    old_session_number = None
    if "current_idx" in data["barber_shop"]:
        data["barber_shop"]["prev_idx"] = data["barber_shop"]["current_idx"]
        data["barber_shop"]["current_idx"] = new_session_number
    else:
        data["barber_shop"]["prev_idx"] = None
        data["barber_shop"]["current_idx"] = new_session_number
    data["barber_shop"]["id"] = client_id
    return data, old_session_number

def load_record(record_version, phone_number, request_data = {}, current_data = {}, combined_paths=[]):
    current_file = os.path.abspath(__file__)
    parent_folder = os.path.abspath(current_file)
    grand_parent_folder = os.path.abspath(parent_folder)
    file_path = "{}/STORAGE_MANAGEMENT/Online_transaction/StoredData/CLIENT/meta-data/client_meta_data.json".format(grand_parent_folder)
    if os.path.exists(file_path):
        with open(file_path, "r") as f_ptr:
            client_meta_file = f_ptr.read()
            client_seq_id = client_meta_file[phone_number]["client_id"]
            session_id = client_meta_file[phone_number]["session_id"]
    if record_version == "CURRENT":
        if phone_number and client_seq_id and session_id:
            file_path = "{}/STORAGE_MANAGEMENT/Online_transaction/StoredData/CLIENT/meta-data/StoreData/{}#{}#{}.json".format(
                client_seq_id, phone_number, session_id
            )
            if os.path.exists(file_path):
                with open(file_path, "r") as f_ptr:
                    client_record = f_ptr.read()
                    return json.loads(client_record), None
            else:
                return None, "RECORD-NOT-FOUND"
    elif record_version == "NEW":
        merged_data = merge_record(request_data, current_data, combined_paths)
    return client_record

def validate_fields(requst_data, end_paths):
    missing_fields = []
    if "modifyFields" in requst_data:
        for each_field in requst_data["modifyFields"]:
            if each_field not in end_paths:
                missing_fields.append(each_field)
        return {"missingFields" : missing_fields, "errMsg" : ""}
    return {"missingFields" : missing_fields, "errMsg" : "field modification not found"}

def update_by_path(data, path, new_value, sep="."):
    keys = path.split(sep)
    d = data
    for key in keys[:-1]:
        d = d.setdefault(key, {})  # move deeper, create dicts if missing
    d[keys[-1]] = new_value       # update final value
    return d

def merge_record(requst_data, loaded_data, combined_paths):
    for each_field in requst_data["modifyFields"]:
        path = combined_paths[each_field]
        new_value = requst_data["modifyFields"][each_field]
        requst_data = update_by_path(requst_data, path, new_value)
    return requst_data

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
