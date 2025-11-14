from fastapi import Request, APIRouter
import httpx
from PROCESS_REQUEST.PROCESS.HelperFunctions import SendResponse
from PROCESS_REQUEST.PROCESS.SessionWiseProcess import add_to_thread

ClientApi = APIRouter()

async def SessionWiseProcess(Action, RequestData):
    Response = await add_to_thread(Action, RequestData)
    return Response

@ClientApi.post("/CreateClient")
async def CreateClient(request: Request):
    async with httpx.AsyncClient() as client:
        request = await request.json()
        Response = await SessionWiseProcess(request, "CREATE-CLIENT")
    return Response

@ClientApi.post("/UpdateClient")
async def UpdateClient(request : Request):
    async with httpx.AsyncClient() as client:
        request = await request.json()
        RequestObj = await SessionWiseProcess(request, "UPDATE-CLIENT")
    return 

@ClientApi.post("/DeleteClient")
async def DeleteClient(request : Request):
    async with httpx.AsyncClient() as client:
        RequestObj = await SessionWiseProcess(request, "DELETE-CLIENT")
    return 

async def log():
    return

