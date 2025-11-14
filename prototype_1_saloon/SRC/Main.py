from fastapi import FastAPI, Request
import httpx
from PROCESS_REQUEST.PROCESS.HelperFunctions import send_major_res, create_threads, destroy_threads, define_uvicorn_run
from PROCESS_REQUEST.PROCESS.ParalllelExec import worker
import threading
from contextlib import asynccontextmanager
from PROCESS_REQUEST.VersionApis import v1_api
from PROCESS_REQUEST.PROCESS.SharedData import max_parallel_requests
from PROCESS_REQUEST.PROCESS.SharedData import i_p, port, reload_uvicorn, log_level_uvicorn
from PROCESS_REQUEST.PROCESS.HelperFunctions import set_routers
from PROCESS_REQUEST.VersionCommon import list_of_child_router

shutdown_event = threading.Event()
client = httpx.AsyncClient()
@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_threads = await create_threads(max_parallel_requests, worker, [])
    yield
    await destroy_threads(shutdown_event, worker_threads, client)
    
App = FastAPI(lifespan=lifespan)

@App.post("/api/v1/makeRequest")
async def ParentRequestHandler(request:Request):
    V1_JsonRequest = await request.json()
    v1_response = await v1_api(App, client, V1_JsonRequest)
    return await send_major_res(v1_response.json())

set_routers(App, list_of_child_router)

if __name__ == "__main__":
    define_uvicorn_run(i_p, port, reload_uvicorn, log_level_uvicorn)

