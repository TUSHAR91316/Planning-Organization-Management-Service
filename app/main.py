from fastapi import FastAPI
from app.db.mongodb import db
from app.api import auth, organizations

app = FastAPI(title="Organization Management Service")

@app.on_event("startup")
async def startup_db_client():
    db.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    db.close()

app.include_router(auth.router, prefix="/admin", tags=["Admin"])
app.include_router(organizations.router, prefix="/org", tags=["Organization"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Organization Management Service"}
