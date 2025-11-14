import threading
import queue
from pathlib import Path

global task_queue
global response_queue
global task_counter
global counter_lock
global test_mode
global client_meta_data
test_mode = True
task_queue = queue.Queue()
counter_lock = threading.Lock()
err_queue = {}
client_meta_data = {}

task_counter = 0
i_p = "127.0.0.1"
port = 8000
host = "http://{}:{}".format(i_p, port)
max_parallel_requests = 1
reload_uvicorn = True
log_level_uvicorn = "debug"
client_schema = '{0}/CLIENT_MANAGEMENT/create_schema.json'.format(Path(__file__).parent)

