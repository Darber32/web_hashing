# from fastapi import Request, HTTPException
# from jose import jwt

# from App.config import settings


# def get_current_user(request: Request):

#     token = request.cookies.get("access_token")

#     if not token:
#         raise HTTPException(status_code=401)

#     payload = jwt.decode(
#         token,
#         settings.SECRET_KEY,
#         algorithms=[settings.ALGORITHM]
#     )

#     return payload["user_id"]



from fastapi import Request, Depends
from App.repositories.user_repository import User_Repository
from App.database import get_db
from App.models.user import User
from jose import jwt
from App.config import settings

class AnonymousUser:
    is_authenticated = False
    role = "guest" 

def get_current_user(request: Request, db=Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return AnonymousUser()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id")
        repo = User_Repository(db)
        user = repo.get_by_id(user_id)

        if user:
            user.is_authenticated = True
            return user

        return AnonymousUser()
    except Exception:
        return AnonymousUser()