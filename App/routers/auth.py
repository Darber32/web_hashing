from fastapi import APIRouter, Depends, Form, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from App.config import settings
from App.database import get_db
from App.repositories.user_repository import User_Repository
from App.services.auth_service import Auth_Service

from urllib.parse import quote
from App.utils.jwt import create_access_token
from datetime import datetime

router = APIRouter(prefix="/auth")


AUTH_COOKIE_NAME = "access_token"
AUTH_COOKIE_MAX_AGE = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def set_access_token_cookie(response: Response, token: str):
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=AUTH_COOKIE_MAX_AGE,
        expires=AUTH_COOKIE_MAX_AGE,
    )


def clear_access_token_cookie(response: Response):
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )


@router.post("/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    repo = User_Repository(db)
    service = Auth_Service(repo)

    user = await service.register(username, email, password)

    if user == None:
        error_msg = quote("Данная электронная почта уже используется") 
        response = RedirectResponse(url="/register", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response


    jwt_token = create_access_token({"user_id": user.id})

    response = RedirectResponse(url="/profile", status_code=303)
    set_access_token_cookie(response, jwt_token)

    return response


@router.post("/login")
def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    repo = User_Repository(db)
    service = Auth_Service(repo)

    user = service.login(email, password)

    if not user:
        error_msg = quote("Неверный адрес электронной почты или пароль") 
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response

    if not user.is_active:
            error_msg = quote("Для входа в аккаунт требуется активировать аккаунт") 
            response = RedirectResponse(url="/login", status_code=303)
            response.set_cookie(key="error_msg", value=error_msg, max_age=1)
            return response

    jwt_token = create_access_token({"user_id": user.id})

    response = RedirectResponse(url="/profile", status_code=303)
    set_access_token_cookie(response, jwt_token)

    return response


@router.get("/confirm/{token}")
def confirm(token: str, db: Session = Depends(get_db)):

    repo = User_Repository(db)

    user = repo.activate(token) 

    if not user:
        return {"error": "Invalid token"}

    if user.token_expiry < datetime.utcnow():
        repo.delete(user.id)
        error_msg = quote("Время действия ссылки истекто") 
        response = RedirectResponse(url="/login", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response


    jwt_token = create_access_token({"user_id": user.id})

    response = RedirectResponse(url="/profile", status_code=303)
    set_access_token_cookie(response, jwt_token)

    return response


@router.post("/logout", name="logout")
def logout(response: Response):

    redirect = RedirectResponse(url="/", status_code=303)
    clear_access_token_cookie(redirect)
    return redirect

