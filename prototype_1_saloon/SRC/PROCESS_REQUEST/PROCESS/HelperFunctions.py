import json
from fastapi.responses import JSONResponse
from . import SharedData
import threading
import os
from pathlib import Path
import uvicorn
from .SharedData import client_schema

async def FindResponse(seq_key, session_key, all_response):
    KeyValue = None
    search_key = "{0}#{1}".format(seq_key, session_key)
    if search_key in all_response:
        return "", all_response[search_key]
    return None, KeyValue

async def SendResponse(Err, Response, seq_key, session_key, thread_name, Queue, phone_number):
    if "clients" in SharedData.client_meta_data:
        SharedData.client_meta_data["clients"][str(phone_number)] = {"client_id" : seq_key, "session_id" : session_key}
    else:
        SharedData.client_meta_data["clients"] = {}
        SharedData.client_meta_data["clients"][str(phone_number)] = {"client_id" : seq_key, "session_id" : session_key}

    temp = Queue.pop("{0}#{1}".format(seq_key, session_key))

    if Err:
        return json.dumps({
            "status" : 400,
            "errMessage":Err,
            "response":Response,
            "seq_key" : seq_key,
            "session_id" : session_key,
            "thread_name" : thread_name
        })
    else:
        return json.dumps({
            "status" : 200,
            "errMessage":None,
            "response":Response,
            "seq_key" : seq_key,
            "session_id" : session_key,
            "thread_name" : thread_name
        })
    

async def ParseData(JsonData):
    if JsonData == "UPDATE-CLIENT":
        return "UpdateClient" 
    elif JsonData == "CREATE-CLIENT":
        return "CreateClient"
    elif JsonData == "DELETE-CLIENT":
        return "DeleteClient"
    return None
    
def FindKeyValue(RequestAttr, OrgData):
    try:
        Err = None
        for ele in OrgData:
            if RequestAttr == ele:
                return OrgData[RequestAttr]
            else:
                if type(OrgData[ele]) == dict:
                    Result, Err = FindKeyValue(RequestAttr, OrgData[ele])
    except Exception as e:
        Result = ""
        Err = e
    return Result, Err

async def get_major_api_division(req):
    division = "client"
    return division

async def get_all_keys(data, prefix=""):
    keys = set()
    if isinstance(data, dict):
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            keys |= get_all_keys(v, full_key)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            keys |= get_all_keys(item, prefix)
    return keys

def find_key_paths(data, target_key, prefix=""):
    paths = ""
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{prefix}.{k}" if prefix else k
            if k == target_key:
                paths = "{0}.{1}".format(paths, current_path)
            paths += find_key_paths(v, target_key, current_path)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            list_path = f"{prefix}[{i}]"
            paths += find_key_paths(item, target_key, list_path)
    return paths

def extract_phn_number(data):
    phone = None
    path = find_key_paths(data, "phone")
    prev_dict = data
    for idx, each_path in enumerate(path.split(".")):
        if each_path:
            prev_dict = prev_dict[each_path]
    return prev_dict

async def ValidateFields(Action, schema, RequestData, LoadedData):
    with (schema, "r") as FilePtr:
        SchemaFile = json.loads(FilePtr.read())
    keys1 = get_all_keys(SchemaFile)
    keys2 = get_all_keys(RequestData)
    missing_fields = []
    if LoadedData:
        for key in LoadedData:
            paths = find_key_paths(RequestData, key)
            #update value
    else:
        #new request
        for each in keys1:
            if each not in keys2:
                missing_fields.append(each)

    if Action == "CREATE-CLIENT":
        #check all fields
        pass
    MissingFields = {
        "tableName" : "",
        "missingFields" : missing_fields
    }

    validated = False

    LoopCount = len(RequestData)

    while LoopCount:
        
        LoopCount -= 1

    return

def LoadData(ReqData):
    PrevData = {}
    return PrevData

async def send_major_res(res):
    if res:
        res_data = json.loads(res)
    else:
        res_data = {}
    if "errMessage" in res_data:
        if res_data["errMessage"]:
            status = 400
        else:
            status = 200
    else:
        status = 200
    return JSONResponse(status_code = status, content = res_data)

async def create_threads(max_parallel_requests, worker, worker_threads):
    if os.path.exists("{0}/STORAGE_MANAGEMENT/Online_transaction/StoredData/CLIENT/meta-data/client_meta_data.json".format(Path(__file__).parent)):
        with open("{0}/STORAGE_MANAGEMENT/Online_transaction/StoredData/CLIENT/meta-data/client_meta_data.json".format(Path(__file__).parent), "r") as f:
            meta_client_rec = f.read()
            if meta_client_rec:
                SharedData.client_meta_data = json.loads(meta_client_rec)
                SharedData.task_counter = SharedData.client_meta_data["last_seq_key"]
    for _ in range(max_parallel_requests):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        worker_threads.append(t)
    return worker_threads


async def destroy_threads(shutdown_event, worker_threads, client):
    print("Shutting down threads...")
    shutdown_event.set()
    for t in worker_threads:
        if t.is_alive():
            t.join(timeout=5)
    await client.aclose()
    print(SharedData.task_counter)
    with open("{0}/STORAGE_MANAGEMENT/Online_transaction/StoredData/CLIENT/meta-data/client_meta_data.json".format(Path(__file__).parent), "w+") as f:
        SharedData.client_meta_data["last_seq_key"] = SharedData.task_counter
        json.dump(SharedData.client_meta_data, f, indent=4)  # indent=4 makes it pretty-printed
    print("All threads terminated cleanly")
    return

async def get_actual_action(request):
    Action = request.get("action", None)
    return await ParseData(Action), request

def set_routers(App, child_routers):
    for each_router in child_routers:
        App.include_router(each_router)
    return

def define_uvicorn_run(host="", port="", reload=False, log_level_uvicorn=""):
    uvicorn.run(
        "Main:App",
        host=host,
        port=port,
        reload=False,
        log_level=log_level_uvicorn
    )

def get_keys_paths(schema, parent_path="", recursive_call = False):
    paths = []
    if isinstance(schema, str):
        return
    for k, v in schema.items():
        path = f"{parent_path}.{k}" if parent_path else k
        if isinstance(v, dict):
            paths.extend(get_keys_paths(v, path, True))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    paths.extend(get_keys_paths(item, f"{path}[{i}]", True))
        paths.append(path)
    return paths

def get_mapped_fields(schema):
    mapped_fields = {
                        "fields" : [],
                        "path"   : {}
                    }
    all_path = get_keys_paths(schema)
    for each_path in all_path:
        field = each_path.split(".")[-1]
        mapped_fields["fields"].append(field)
        mapped_fields["path"][field] = each_path
    return mapped_fields

def read_record(filename):

    file_data = {}
    file = ""

    if filename == "create_schema":
        file = client_schema

    if os.path.exists(file):
        with open(file, "r") as f_ptr:
            file_data = f_ptr.read()
            if file_data:
                return json.loads(file_data)
            return file_data
    else:
        return file_data
    


