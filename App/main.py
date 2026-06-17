from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from App.routers import admin, auth, pages, edit, hash

app = FastAPI()

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(admin.router)
app.include_router(edit.router)
app.include_router(hash.router)
app.mount("/static", StaticFiles(directory="App/static"), name="static")
