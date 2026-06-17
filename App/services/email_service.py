import aiosmtplib
from email.message import EmailMessage

from App.config import settings


class Email_Service:

    async def send_confirmation(self, email: str, token: str):

        link = f"http://localhost:8000/auth/confirm/{token}"

        message = EmailMessage()

        message["From"] = settings.SMTP_EMAIL
        message["To"] = email
        message["Subject"] = "Подтвердите свой аккаунт"

        message.set_content(
            f"""
Добро пожаловать!

Чтобы подтвердить свой аккаунт, перейдите по ссылке ниже:

{link}
"""
        )

        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD
        )

    async def send_email_change(self, old_email: str, new_email: str, token: str):
        link = f"http://localhost:8000/edit/confirm_email/{token}"

        message = EmailMessage()

        message["From"] = settings.SMTP_EMAIL
        message["To"] = old_email
        message["Subject"] = "Подтвердите смену электронной почты"

        message.set_content(
            f"""
Вы действительно хотите сметить адрес электронной почты на {new_email}?

Чтобы подтвердить, перейдите по ссылке ниже:

{link}
"""
        )

        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD
        )

    async def send_pass_change(self, email: str, token: str):
        link = f"http://localhost:8000/edit/confirm_password/{token}"

        message = EmailMessage()

        message["From"] = settings.SMTP_EMAIL
        message["To"] = email
        message["Subject"] = "Подтвердите смену пароля"

        message.set_content(
            f"""
Вы действительно хотите изменить пароль?

Чтобы подтвердить, перейдите по ссылке ниже:

{link}
"""
        )

        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD
        )

    async def send_pass_reset(self, email: str, token: str):
        link = f"http://localhost:8000/edit/reset_password/{email}&{token}"

        message = EmailMessage()

        message["From"] = settings.SMTP_EMAIL
        message["To"] = email
        message["Subject"] = "Подтвердите сброс пароля"

        message.set_content(
            f"""
Вы действительно хотите сбросить пароль?

Чтобы подтвердить, перейдите по ссылке ниже:

{link}
"""
        )

        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD
        )