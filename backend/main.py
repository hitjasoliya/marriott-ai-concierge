from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import init_db
from app.embeddings.model import warm_up_embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    warm_up_embedding_model()
    yield


app = FastAPI(title="Marriott AI Concierge", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}
