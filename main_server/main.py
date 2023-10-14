import httpx
from fastapi import FastAPI, HTTPException

from utils import get_containers_address_in_network, LOGGER

app = FastAPI()
data = []


@app.get("/all")
def read_all():
    return {"main data": data}


@app.post("/append", status_code=201)
def add_number(num: int):

    containers = get_containers_address_in_network('data_network')
    hard_urls = [f"http://{container_id}:8000/append" for container_id in containers]

    replication_count = 0

    for url in hard_urls:
        r = httpx.post(
            url=url,
            params={"num": num}
        )
        if r.status_code == 200:
            replication_count += 1
    data.append(num)

    if replication_count != len(containers):
        raise HTTPException(status_code=500, detail="Unable to replicate")

    LOGGER.info("successfully replicated to all nodes")
    return {"Message": "Appended number"}
