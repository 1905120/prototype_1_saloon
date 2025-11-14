from .PROCESS.HelperFunctions import get_actual_action, set_routers
from . import VersionCommon
from .PROCESS.SharedData import host

async def v1_api(App, client, request):
    ActualAction, JsonRequest = await get_actual_action(request)
    response = await client.post("{}/{}".format(host, ActualAction), json=JsonRequest)
    return response

