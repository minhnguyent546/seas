import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import EmailStr

import app.utils as app_utils
from app.api import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.health import check_health
from app.schemas import MessageResponse

_start_time = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    logger.info('"Starting application...')
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    _start_time = time.time()
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


app = FastAPI(title="FastAPI", lifespan=lifespan)

# static
app.mount(path="/static", app=StaticFiles(directory="static"), name="static")

# jinja2 template
templates = Jinja2Templates(directory="templates")

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["utils"])
async def health_check():
    return await check_health()


@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)


@app.get(
    f"{settings.API_PREFIX}/html", response_class=HTMLResponse, tags=["utils"]
)
async def html(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="example.html",
        context={"title": "SEAS"},
    )


@app.get(
    f"{settings.API_PREFIX}/test-send-email",
    response_model=MessageResponse,
    tags=["utils"],
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


app.include_router(api_router, prefix=settings.API_PREFIX)


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=settings.API_PORT)
