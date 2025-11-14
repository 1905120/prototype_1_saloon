#Api for central system
import httpx
from fastapi import FastAPI

app = FastAPI()

@app.get("/external")
async def fetch_external():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/todos/1")
        return response.json()

