import os
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import EmailStr
from starlette.middleware.sessions import SessionMiddleware

import app.utils as app_utils
from app.api import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.health import check_health
from app.schemas import MessageResponse
from app.utils import custom_generate_unique_id

_start_time = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    logger.info('"Starting application...')
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    _start_time = time.time()

    if not os.path.isdir(settings.DOC_UPLOAD_DIR):
        os.makedirs(settings.DOC_UPLOAD_DIR)

    try:
        async with AsyncSessionLocal() as session:  # pyright: ignore[reportGeneralTypeIssues]
            await init_db(session)

        yield
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during startup",
        ) from e
    finally:
        # clean up here
        pass


app = FastAPI(
    title="FastAPI",
    lifespan=lifespan,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# static
app.mount(path="/static", app=StaticFiles(directory="static"), name="static")

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# session middleware (for OAuth2)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["utils"])
async def health_check():
    return await check_health()


@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)


@app.get(
    f"{settings.API_PREFIX}/test-send-email",
    response_model=MessageResponse,
    tags=["utils"],
    include_in_schema=(settings.ENVIRONMENT == "development"),
)
async def test_send_email(email_to: EmailStr):
    """Test sending email"""
    test_email_data = app_utils.generate_test_email(email_to=email_to)
    app_utils.send_email(
        email_to=email_to,
        subject=test_email_data.subject,
        html_content=test_email_data.html_content,
    )
    return MessageResponse(message="Test email sent")


@app.get(
    f"{settings.API_PREFIX}/test-send-email-background",
    response_model=MessageResponse,
    tags=["utils"],
    include_in_schema=(settings.ENVIRONMENT == "development"),
)
async def test_send_email_background(
    background_tasks: BackgroundTasks, email_to: EmailStr
):
    """Test sending email using FastAPI background tasks"""
    test_email_data = app_utils.generate_test_email(email_to=email_to)
    app_utils.send_email_in_background(
        background_tasks=background_tasks,
        email_to=email_to,
        subject=test_email_data.subject,
        html_content=test_email_data.html_content,
    )
    return MessageResponse(message="Test email sent in background")


app.include_router(api_router, prefix=settings.API_PREFIX)


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=settings.API_PORT)
