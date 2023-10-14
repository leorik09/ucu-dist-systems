import time

from fastapi import FastAPI

app = FastAPI()
data = []


@app.get("/all")
def read_all():
    return {"secondary list": data}


@app.post("/append")
def add_number(num: int):
    data.append(num)
    time.sleep(1)

    return {"message": "Added"}
