import httpx
import asyncio
import threading
from fastapi import FastAPI, HTTPException, Response, status
from utils import get_containers_address_in_network, LOGGER
from datetime import datetime

app = FastAPI()
data = []
numeric_values = set()


@app.get("/all")
def read_all():
    data_repr = [item["num"] for item in data]
    return {"main data": data_repr}


async def replicate_on_secondary(client: httpx.AsyncClient, url: str, item: dict):
    LOGGER.info(f"Calling {url}.")
    r = await client.post(
        url=url,
        timeout=100,
        params=item
    )
    if r.status_code == 201:
        LOGGER.info(f"Replication to {url} is successful.")
    if r.status_code == 304:
        LOGGER.info(f"Replication to {url} failed. Duplicate value")
    return r


async def replicate_all(hard_urls: list, item: dict, write_concern: int):

    async with httpx.AsyncClient() as client:
        tasks = [replicate_on_secondary(client, url, item) for url in hard_urls]

        is_completed = 0
        for task in asyncio.as_completed(tasks):
            result = await task
            LOGGER.info(f'Tasks result: {(result)}')
            is_completed += 1
            if is_completed == write_concern - 1:
                LOGGER.info("Successfully waited for wc")
                return write_concern


def run_async_in_thread(hard_urls, num, write_concern):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(replicate_all(hard_urls, num, write_concern))
    loop.close()


@app.post("/append", status_code=201)
async def add_number(num: int, write_concern: int, response: Response):
    item = {"num": num, "timestamp": str(datetime.now())}

    containers = get_containers_address_in_network('data_network')
    hard_urls = [f"http://{container_id}:8000/append" for container_id in containers]

    if num in numeric_values:
        response.status_code = status.HTTP_304_NOT_MODIFIED
        return response

    numeric_values.add(num)
    data.append(item)
    replication_count = 1

    if write_concern == 1:
        thread = threading.Thread(target=run_async_in_thread, args=[hard_urls, item, write_concern])
        thread.start()
    else:
        replication_count = await replicate_all(hard_urls, item, write_concern)

    if replication_count != write_concern:
        raise HTTPException(status_code=500, detail="Unable to replicate")

    LOGGER.info("successfully replicated to all nodes")
    return {"message": "Appended number"}
