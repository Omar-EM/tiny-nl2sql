from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.chat import chat_router


app = FastAPI(
    title="NL2SQL Agent API",
    description="A RAG-powered AI agent that translates natural langugae into SQL for live db querying",
    version="0.1.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

app.include_router(chat_router)
