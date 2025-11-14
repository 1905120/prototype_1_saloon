from fastapi import Request, APIRouter
from PROCESS_REQUEST.PROCESS.SessionWiseProcess import add_to_thread

ClientApi = APIRouter()

async def SessionWiseProcess(Action, RequestData):
    return await add_to_thread(Action, RequestData)

@ClientApi.post("/CreateClient")
async def CreateClient(request: Request):
    request = await request.json()
    return await SessionWiseProcess(request, "CREATE-CLIENT")

@ClientApi.post("/UpdateClient")
async def UpdateClient(request : Request):
    request = await request.json()
    return await SessionWiseProcess(request, "UPDATE-CLIENT")

@ClientApi.post("/DeleteClient")
async def DeleteClient(request : Request):
    Response = await SessionWiseProcess(request, "DELETE-CLIENT")
    return Response

async def log():
    return

