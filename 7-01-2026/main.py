
from fastapi import FastAPI
from routes import router
from database import init_collection

app = FastAPI(title="Vector Search API")

init_collection()
app.include_router(router)
