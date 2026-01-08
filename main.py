
from fastapi import FastAPI
from routes import router
from database import init_collection

app = FastAPI()

init_collection()
app.include_router(router)
