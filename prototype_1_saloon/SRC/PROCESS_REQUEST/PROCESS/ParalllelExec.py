import threading
from .SharedData import task_queue

def worker():
    while True:
        keys, method_call, RequestData = task_queue.get()
        if RequestData:
            response = method_call(RequestData, threading.current_thread().name)
            task_queue.task_done()


