from fastapi import APIRouter, Depends, Form, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from App.database import get_db
from App.repositories.user_repository import User_Repository
from App.utils.dependencies import get_current_user

from App.utils.security import create_token, verify_password, hash_password
from App.services.email_service import Email_Service
from datetime import datetime, timedelta

from urllib.parse import quote
from App.config import settings

router = APIRouter(prefix="/edit")

@router.post('/username')
def edit_username(
    response: Response,
    username: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    repo = User_Repository(db)
    user = repo.edit_username(current_user.id, username)

    return RedirectResponse(url="/profile", status_code=303)


@router.post('/email')
async def email_username(
    response: Response,
    email: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    repo = User_Repository(db)
    alreadry_exist = repo.get_by_email(email)
    if alreadry_exist:
        error_msg = quote("Данная электронная почта уже используется") 
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response

    token = create_token()
    token_expiry = datetime.utcnow() + timedelta(minutes=settings.CONFIRM_TOKEN_EXPIRE_MINUTES)
    repo.add_token_email(current_user.id, token, token_expiry, email)

    email_service = Email_Service()
    await email_service.send_email_change(current_user.email, email, token)
    return RedirectResponse(url="/profile", status_code=303)

@router.get('/confirm_email/{token}')
def confirm_email(token: str, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    repo = User_Repository(db)
    user = repo.get_by_token(token)
    
    if user.token_expiry < datetime.utcnow():
        repo.reset_token(user.id)
        error_msg = quote("Время действия ссылки истекло") 
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response

    user = repo.edit_email(token)

    return RedirectResponse(url="/profile", status_code=303)


@router.post('/password')
async def password_username(
    response: Response,
    old_pass: str = Form(...),
    new_pass: str = Form(...),
    repeat_pass: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    repo = User_Repository(db)
    if new_pass != repeat_pass:
        error_msg = quote("Новые пароли не совпадают") 
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response
    if old_pass == new_pass:
        error_msg = quote("Новый пароль совпадает со старым") 
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response
    if not verify_password(old_pass, current_user.password):
        error_msg = quote("Введён неверный пароль") 
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response

    token = create_token()
    token_expiry = datetime.utcnow() + timedelta(minutes=settings.CONFIRM_TOKEN_EXPIRE_MINUTES)
    repo.add_token_password(current_user.id, token, token_expiry, hash_password(new_pass))
    email_service = Email_Service()
    await email_service.send_pass_change(current_user.email, token)
    return RedirectResponse(url="/profile", status_code=303)

@router.get('/confirm_password/{token}')
def confirm_email(token: str, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    repo = User_Repository(db)
    user = repo.get_by_token(token)

    if user.token_expiry < datetime.utcnow():
        repo.reset_token(user.id)
        error_msg = quote("Время действия ссылки истекло") 
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response

    user = repo.edit_password(token)

    return RedirectResponse(url="/profile", status_code=303)


@router.post('/reset_password')
async def reset_password(response: Response,
    email: str = Form(...),
    new_pass: str = Form(...),
    repeat_pass: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    repo = User_Repository(db)
    if new_pass != repeat_pass:
        error_msg = quote("Пароли не совпадают") 
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response

    token = create_token()
    token_expiry = datetime.utcnow() + timedelta(minutes=settings.CONFIRM_TOKEN_EXPIRE_MINUTES)
    repo.add_token_password_by_email(email, token, token_expiry, hash_password(new_pass))
    email_service = Email_Service()
    await email_service.send_pass_reset(email, token)
    return RedirectResponse(url="/profile", status_code=303)

@router.get('/reset_password/{email}&{token}')
def confirm_email(email: str,
    token: str,
    db: Session = Depends(get_db),
):

    repo = User_Repository(db)
    user = repo.get_by_token(token)

    if user.token_expiry < datetime.utcnow():
        repo.reset_token_by_email(email)
        error_msg = quote("Время действия ссылки истекло") 
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="error_msg", value=error_msg, max_age=1)
        return response

    user = repo.edit_password(token)

    return RedirectResponse(url="/login", status_code=303)