
import uuid
from . import SharedData
from .Process import manage_client_data
from .HelperFunctions import FindResponse, SendResponse
import time

async def get_next_id(Action):
    if Action == "CREATE-CLIENT":
        with SharedData.counter_lock:
            SharedData.task_counter += 1
            return SharedData.task_counter

async def add_to_thread(RequestData, Action):
    seq_id = await get_next_id(Action)
    keys = {"seqId" : seq_id,"sessionKey" : str(uuid.uuid4())}
    ClientRequest = manage_client_data(keys, Action, RequestData)
    if Action == "CREATE-CLIENT":
        SharedData.task_queue.put((keys, ClientRequest.create_client, RequestData))
    elif Action == "DELETE-CLIENT":
        SharedData.task_queue.put((keys, ClientRequest.delete_client, RequestData))
    elif Action == "UPDATE-CLIENT":
        SharedData.task_queue.put((keys, ClientRequest.update_client, RequestData))
    check_response = 3
    while check_response:
        Err, Response = await FindResponse(ClientRequest.seq_key, ClientRequest.session_key, SharedData.response_queue)
        if Response:
            break
        time.sleep(0.3)
        check_response -= 1
    if not(check_response):
        Err = "Request Failed"
        time.sleep(1)
        Response = None
    return await SendResponse(Err, Response, ClientRequest.seq_key, ClientRequest.session_key, ClientRequest.thread_name, SharedData.response_queue, ClientRequest.phone_number)

