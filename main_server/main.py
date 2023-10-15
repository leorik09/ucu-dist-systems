import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from utils import get_containers_address_in_network, LOGGER

app = FastAPI()
data = []


@app.get("/all")
def read_all():
    return {"main data": data}


async def replicate_on_secondary(client: httpx.AsyncClient, url: str, num: int):
    LOGGER.info(f"Calling {url}.")
    r = await client.post(
        url=url,
        params={"num": num}
    )
    if r.status_code == 200:
        LOGGER.info(f"Replication to {url} is successful.")
    return r


async def replicate_all(hard_urls: list, num: int):
    async with httpx.AsyncClient() as client:
        tasks = [replicate_on_secondary(client, url, num) for url in hard_urls]
        result = await asyncio.gather(*tasks)
        LOGGER.info(f'result: {result}')
    return sum(1 if r.status_code == 200 else 0 for r in result)


@app.post("/append", status_code=201)
async def add_number(num: int):

    containers = get_containers_address_in_network('data_network')
    hard_urls = [f"http://{container_id}:8000/append" for container_id in containers]

    replication_count = await replicate_all(hard_urls, num)

    data.append(num)

    if replication_count != len(containers):
        raise HTTPException(status_code=500, detail="Unable to replicate")

    LOGGER.info("successfully replicated to all nodes")
    return {"Message": "Appended number"}
