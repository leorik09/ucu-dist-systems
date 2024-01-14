import httpx
import asyncio
import threading
import random
from fastapi import FastAPI, HTTPException, Response, BackgroundTasks, status
from fastapi_utils.tasks import repeat_every
from utils import get_containers_address_in_network, LOGGER
from datetime import datetime

app = FastAPI()
data = []
numeric_values = set()

CONTAINERS = get_containers_address_in_network('data_network')
HARD_URLS = sorted([f"http://{container_id}:8000/append" for container_id in CONTAINERS])

dead_containers = []

async def retry(client, url, item):
    l = random.randint(1, 5)
    eps = 2

    while True:
        await asyncio.sleep(l+eps)
        l = random.randint(1, 5)
        eps *= 1.2

        live_containers = get_containers_address_in_network('data_network')
        live_urls = [f"http://{container_id}:8000/append" for container_id in live_containers]

        if url not in live_urls:
            continue

        LOGGER.info(f"\nRetrying post for url: {url}...\n")
        try:
            r = await client.post(
                    url=url,
                    timeout=100,
                    params=item
                )
            LOGGER.info(f"Retry response from {url}. Status_code: {r.status_code}")
            if r.status_code in [201, 304]:
                LOGGER.info(f"Retry: Complete")
                return r
        except RuntimeError as e:
            print(e)
            continue


async def replicate_on_secondary(client: httpx.AsyncClient, url: str, item: dict, background_tasks: BackgroundTasks):
    LOGGER.info(f"Calling {url}.")
    r = await client.post(
        url=url,
        timeout=100,
        params=item
    )
    LOGGER.info(f"Response from {url}. Status_code: {r.status_code}")
    if r.status_code not in [201, 304]:

        if url not in list(map(lambda x: x['url'], dead_containers)):
            container = {
                'url': url,
                'timestamp': item['timestamp']
            }
            dead_containers.append(container)
        background_tasks.add_task(retry, client, url, item)
    return r


async def replicate_all(hard_urls: list, item: dict, write_concern: int, background_tasks: BackgroundTasks):

    async with httpx.AsyncClient() as client:
        tasks = [replicate_on_secondary(client, url, item, background_tasks) for url in hard_urls]

        is_completed = 0
        for task in asyncio.as_completed(tasks):
            result = await task
            LOGGER.info(f'Tasks result: {(result)}')
            is_completed += 1
            if is_completed == write_concern - 1:
                LOGGER.info("Successfully waited for wc")
                return write_concern


def run_async_in_thread(hard_urls, num, write_concern, background_tasks):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(replicate_all(hard_urls, num, write_concern, background_tasks))
    loop.close()


@app.post("/append", status_code=201)
async def add_number(num: int, write_concern: int, response: Response, background_tasks: BackgroundTasks):
    request_timestamp = str(datetime.now())
    item = {"num": num, "timestamp": request_timestamp}

    live_containers = get_containers_address_in_network('data_network')
    hard_urls = [f"http://{container_id}:8000/append" for container_id in live_containers]

    ct = sorted(hard_urls + list(map(lambda x: x['url'], dead_containers)))
    if HARD_URLS != ct:
        for container_url in set(HARD_URLS).difference(set(ct)):
            container = {
                'url': container_url,
                'timestamp': request_timestamp
            }
            dead_containers.append(container)

    if num in numeric_values:
        response.status_code = status.HTTP_304_NOT_MODIFIED
        return response

    numeric_values.add(num)
    data.append(item)
    replication_count = 1

    if write_concern == 1:
        thread = threading.Thread(target=run_async_in_thread, args=[hard_urls, item, write_concern, background_tasks])
        thread.start()
    else:
        replication_count = await replicate_all(hard_urls, item, write_concern, background_tasks)

    if replication_count != write_concern:
        raise HTTPException(status_code=500, detail="Unable to replicate")

    LOGGER.info("successfully replicated to all nodes")
    return {"message": "Appended number"}


@app.get("/all")
def read_all():
    data_repr = [item["num"] for item in data]
    return {"main data": data_repr}


@app.on_event("startup")
@repeat_every(seconds=30)
async def sync_all() -> None:
    LOGGER.info(f"sync_all dead_containers: {dead_containers}")

    containers_to_remove = set()
    async with httpx.AsyncClient() as client:
        for container in dead_containers:
            url = container['url']
            timestamp = container['timestamp']

            missed_data = list(filter(lambda x: x['timestamp'] >= timestamp, data))
            LOGGER.info(f"Missed data for {url}: {missed_data}")

            for item in missed_data:
                r = await client.post(
                    url=url,
                    timeout=100,
                    params=item
                )
                LOGGER.info(f"Response from {url}. Status_code: {r.status_code}")
                if r.status_code in [201, 304]:
                    containers_to_remove.add(container)

        for item in containers_to_remove:
            dead_containers.remove(item)
