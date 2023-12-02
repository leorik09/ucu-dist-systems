import random
from fastapi import FastAPI, Response, status
import logging
import asyncio
LOGGER = logging.getLogger(__name__)

app = FastAPI()
data = []
numeric_values = set()


@app.get("/all")
def read_all():
    data_repr = [item["num"] for item in data]
    return {"secondary list": data_repr}


@app.post("/append", status_code=201)
async def add_number(num: int, timestamp: str, response: Response):
    item = {"num": num, "timestamp": timestamp}
    await asyncio.sleep(random.randint(5,20))
    if num not in numeric_values:
        numeric_values.add(num)
        data.append(item)
        data.sort(key=lambda x: x["timestamp"])
        return {"message": "Added"}

    response.status_code = status.HTTP_304_NOT_MODIFIED
    return {"message": "Duplicate value"}
