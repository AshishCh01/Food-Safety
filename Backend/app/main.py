import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import MaxBodySizeMiddleware
from app.utils.exceptions import AppError

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s starting up in %s mode", settings.app_name, settings.environment)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Registered before error_handling_middleware below (and therefore ends up
# INNERMOST of the three custom layers here, closest to routing - see that
# function's docstring for the general prepend-reverses-order rule). This
# positioning is load-bearing, not just ordering-for-ordering's-sake: a
# custom exception raised while reading an oversized streamed body (no
# unregistered exception handler exists for it) needs to reach
# MaxBodySizeMiddleware's own try/except before it would otherwise be
# swallowed as a generic 500 by error_handling_middleware's broader
# `except Exception` a layer further out.
app.add_middleware(MaxBodySizeMiddleware)


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Adds baseline security headers to every response
    (docs/SECURITY_AND_RBAC.md section 11, "security headers at the edge")
    and is also the primary catch-all for exceptions not already mapped to
    an AppError/HTTPException/RequestValidationError.

    Registration order matters here and is easy to get backwards:
    `Starlette.add_middleware()` (which this decorator calls under the hood)
    *prepends* to the middleware list, so the LAST-registered middleware
    ends up OUTERMOST at request time. This function is registered before
    CORSMiddleware below specifically so CORSMiddleware ends up outermost,
    wrapping this one.

    That matters because Starlette always pulls a handler registered for the
    bare `Exception` type (`@app.exception_handler(Exception)` below) out of
    ExceptionMiddleware and into ServerErrorMiddleware, which sits outside
    *every* user middleware, CORS included - so relying on that handler
    alone would send an unhandled-exception response with no CORS headers
    at all, and a cross-origin caller (the React frontend) would see an
    opaque CORS/network failure instead of our JSON error body. Catching the
    exception here instead - inside CORSMiddleware - means the response we
    build still passes back out through CORSMiddleware and gets proper CORS
    headers. `@app.exception_handler(Exception)` is kept only as a
    last-resort fallback for anything that throws outside this middleware's
    call_next (e.g. within CORSMiddleware itself).
    """
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled exception while processing %s %s", request.method, request.url.path)
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                    "details": None,
                    "request_id": None,
                }
            },
        )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Registered after error_handling_middleware so it ends up OUTERMOST (see
# that function's docstring for why this ordering is load-bearing).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": None,
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": None,
                "request_id": None,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data.",
                "details": jsonable_encoder(exc.errors()),
                "request_id": None,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort fallback - error_handling_middleware above is the primary
    catch-all (and the one that guarantees CORS headers on the response, see
    its docstring). This handler only fires for something that throws
    outside that middleware's call_next, e.g. within CORSMiddleware itself.
    Kept so the API never falls through to Starlette's default plain-text
    500 response, which would break the consistent error envelope
    (docs/API_ARCHITECTURE.md section 4) and could leak stack traces in a
    misconfigured debug environment."""
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": None,
                "request_id": None,
            }
        },
    )


app.include_router(api_router)
