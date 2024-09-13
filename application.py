from typing import Union

from pydantic import BaseModel
from fastapi import FastAPI

app = FastAPI()


class User(BaseModel):
    first_name: str
    last_name: str

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/user")
def write_user(user: User):
    return user
