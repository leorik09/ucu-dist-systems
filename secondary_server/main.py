import time
import random
from fastapi import FastAPI

app = FastAPI()
data = []


@app.get("/all")
def read_all():
    return {"secondary list": data}


@app.post("/append")
async def add_number(num: int):
    data.append(num)
    time.sleep(random.randint(1,3))

    return {"message": "Added"}
