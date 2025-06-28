# File: main.py
print("--- main.py: Script execution started ---") # ADD THIS LINE

from fastapi import FastAPI, Depends
# ... rest of the file
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import router as api_router
from core.auth import verify_firebase_token

app = FastAPI(
    title="Secure Investigation & Intelligence Platform (SIIP)",
    description="Backend services for the SIIP application.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/query", dependencies=[Depends(verify_firebase_token)])

@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "SIIP Backend is running"}