from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_file():
    return {
        "lines": [],
    }
