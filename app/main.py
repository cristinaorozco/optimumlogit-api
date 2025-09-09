from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Optimum Logit API", version="0.1.0")

ALLOWED_ORIGINS = [
    "https://tuapp.streamlit.app",
    "https://www.optimumlogit.com",
    "https://app.optimumlogit.com",  # para el futuro
    "http://localhost:8501",         # para pruebas locales de Streamlit
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"hello": "Optimum Logit API", "docs": "/docs", "health": "/healthz"}

@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "mapbox_token_set": bool(os.getenv("MAPBOX_TOKEN"))
    }
