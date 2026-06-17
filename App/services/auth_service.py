from App.repositories.user_repository import User_Repository
from App.utils.security import hash_password, verify_password, create_token
from App.services.email_service import Email_Service
from App.config import settings
from datetime import datetime, timedelta


class Auth_Service:

    def __init__(self, repo: User_Repository):
        self.repo = repo

    async def register(self, username: str, email: str, password: str):

        existing = self.repo.get_by_email(email)

        if existing:
            return None

        token = create_token()
        token_expiry = datetime.utcnow() + timedelta(minutes=settings.CONFIRM_TOKEN_EXPIRE_MINUTES)

        user = self.repo.create(
            username=username,
            email=email,
            password=hash_password(password),
            token=token,
            token_expiry=token_expiry
        )

        email_service = Email_Service()
        await email_service.send_confirmation(email, token)

        return user

    def login(self, email: str, password: str):

        user = self.repo.get_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.password):
            return None

        return user