from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OT Tag Registry API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/test")
async def test() -> dict[str, str]:
    return {"message": "hello world"}
