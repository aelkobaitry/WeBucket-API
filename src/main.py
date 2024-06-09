from fastapi import FastAPI
from config import Settings

app = FastAPI(title=Settings.PROJECT_NAME, version=Settings.PROJECT_VERSION)

# fastapi dev main.py

# TODO: connect jira and bitbucket
# TODO: write short README.md

#ATBBvJBPPmp3EdZx6CgPmbCmBLBs85C28A58


@app.get("/")
async def root():
    return {"Hello": "World"}


@app.get("/ping")
async def root():
    return {"ping": "pong"}
