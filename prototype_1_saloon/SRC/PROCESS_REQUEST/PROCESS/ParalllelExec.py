import threading
from . import SharedData
import json

def worker():
    while True:
        future, method_call, RequestData = SharedData.task_queue.get()
        if RequestData:
            Err = ""
            try:
                processed_seq_id, processed_session_id, processed_phone_number, response = method_call(RequestData, threading.current_thread().name)
                Err = None
            except Exception as Err:
                pass
            finally:
                if "clients" in SharedData.client_meta_data:
                    SharedData.client_meta_data["clients"][str(processed_phone_number)]["session_id"] = processed_session_id
                else:
                    SharedData.client_meta_data["clients"] = {}
                    SharedData.client_meta_data["clients"][str(processed_phone_number)] = {"client_id" : processed_seq_id, "session_id" : processed_session_id}

                if Err:
                    worker_task_response = {
                        "status" : 400,
                        "errMessage":Err,
                        "response":response,
                        "seq_key" : processed_seq_id,
                        "session_id" : processed_session_id,
                        "thread_name" : threading.current_thread().name
                    }
                else:
                    worker_task_response = {
                        "status" : 200,
                        "errMessage":None,
                        "response":response,
                        "seq_key" : processed_seq_id,
                        "session_id" : processed_session_id,
                        "thread_name" : threading.current_thread().name
                    }
                future.set_result(worker_task_response)
                SharedData.task_queue.task_done()

