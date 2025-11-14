
import uuid
from . import SharedData
from .Process import manage_client_data
from .HelperFunctions import extract_phn_number
import asyncio

async def get_next_id(Action):
    if Action == "CREATE-CLIENT":
        with SharedData.counter_lock:
            SharedData.task_counter += 1
            return SharedData.task_counter

async def add_to_thread(RequestData, Action):
    try:
        seq_id                        = await get_next_id(Action)
        phone_number, err_msg         = extract_phn_number(RequestData)
        session_id                    = str(uuid.uuid4())
        err_key                       = "{}#{}".format(phone_number, session_id)
        keys                          = {"seqId" : seq_id, "sessionKey" : session_id, "phoneNumber" : phone_number, "errKey" : err_key}
        SharedData.err_queue[err_key] = []
        loop                          = asyncio.get_running_loop()
        future                        = loop.create_future()
        ClientRequest = manage_client_data(keys, Action, RequestData)
        if session_id and phone_number:
            if Action == "CREATE-CLIENT":
                SharedData.task_queue.put((future, ClientRequest.create_client, RequestData))
            elif Action == "DELETE-CLIENT":
                SharedData.task_queue.put((future, ClientRequest.delete_client, RequestData))
            elif Action == "UPDATE-CLIENT":
                SharedData.task_queue.put((future, ClientRequest.update_client, RequestData))
        else:
            raise Exception(err_msg)
    except Exception as e:
        SharedData.err_queue[err_key].append(e)

    return await future

