import random
from fastapi import FastAPI
import logging
import asyncio
LOGGER = logging.getLogger(__name__)

app = FastAPI()
data = []


@app.get("/all")
def read_all():
    data_repr = [item["num"] for item in data]
    return {"secondary list": data_repr}


@app.post("/append")
async def add_number(num: int, timestamp: str):
    item = {"num": num, "timestamp": timestamp}
    await asyncio.sleep(random.randint(5,20))
    data.append(item)

    data.sort(key=lambda x: x["timestamp"])

    return {"message": "Added"}
