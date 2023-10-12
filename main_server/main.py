from fastapi import FastAPI
import httpx

app = FastAPI()

list = []
@app.get("/all")
def read_all():
    return {"main list": list}

@app.post("/append")
def add_number(num: int):
    list.append(num)

    hard_urls = [f"http://secondary-{i}:8000/append" for i in range(1, 3)]
    for url in hard_urls:
        r = httpx.post(
            url=url,
            params={"num": num}
        )
        if r.status_code == 200:
            continue

    return {"r.status_code": "Appended"}

