from fastapi import APIRouter, Depends, HTTPException, status
from app.db.mongodb import db
from app.schemas.schemas import AdminLogin, Token
from app.core.security import verify_password, create_access_token
from datetime import timedelta
from app.core.config import settings

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(login_data: AdminLogin):
    master_db = db.get_master_db()
    user = await master_db.admins.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email'], "org_name": user['organization_name']},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
