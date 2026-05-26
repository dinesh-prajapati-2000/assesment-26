from fastapi import FastAPI

from app.api.routes import auth, categories, health, products
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

app = FastAPI(title=settings.app_name, debug=settings.debug)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
