from fastapi import FastAPI
import uvicorn


app = FastAPI()

list = []
@app.get("/all")
def read_all():
    return {"secondary list": list}

@app.post("/append")
def add_number(num: int):
    list.append(num)

    import time
    time.sleep(1)

    return {"message": "Added"}

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=4000)
