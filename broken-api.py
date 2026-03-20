"""
Broken API — A FastAPI application with excellent documentation but deliberately broken implementation.

This API serves as a functional test case for DriveBy's Documentation-Driven Testing (DDT) framework.
Static validation (P001-P005, P008-P009) should pass, but functional testing (P006) should fail because
the handlers are intentionally buggy: 500 errors, wrong schemas, and artificial timeouts.
"""

import time
import uuid
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Models — well-documented with Field() examples
# ---------------------------------------------------------------------------

class WidgetCreate(BaseModel):
    """Schema for creating a new widget."""

    name: str = Field(..., example="Turbo Widget", description="Widget display name")
    category: str = Field(..., example="electronics", description="Widget category")
    price: float = Field(..., gt=0, example=29.99, description="Price in USD")


class Widget(WidgetCreate):
    """Full widget representation returned by the API."""

    id: str = Field(..., example="w-001", description="Unique widget identifier")
    created_at: str = Field(
        ..., example="2024-01-15T10:30:00Z", description="ISO 8601 creation timestamp"
    )


class WidgetList(BaseModel):
    """Paginated list of widgets."""

    widgets: List[Widget] = Field(..., description="List of widget objects")
    total: int = Field(..., example=1, description="Total number of widgets")


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error: str = Field(..., example="Not found", description="Error message")
    code: int = Field(..., example=404, description="HTTP status code")
    details: Optional[str] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str = Field(..., example="healthy", description="Service health status")


class DeleteResponse(BaseModel):
    """Confirmation of a successful deletion."""

    message: str = Field(..., example="Widget deleted", description="Deletion confirmation message")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Broken API",
    version="1.0.0",
    description=(
        "A widget management API with intentionally broken handlers.\n\n"
        "## Purpose\n"
        "This API exists to validate that DriveBy can distinguish between "
        "good *documentation* and broken *implementation*. Static analysis "
        "should pass; functional tests should fail.\n\n"
        "## Versioning\n"
        "This API follows semantic versioning. The current version is **1.0.0**. "
        "All endpoints are prefixed with the major version in the path where applicable. "
        "Breaking changes will increment the major version number.\n\n"
        "## Authentication\n"
        "All endpoints (except `/test/health`) require an `X-API-Key` header."
    ),
)


# ---------------------------------------------------------------------------
# Security — API key dependency
# ---------------------------------------------------------------------------

async def verify_auth(x_api_key: str = Header(..., description="API key for authentication")):
    """Validate the X-API-Key header."""
    if x_api_key != "driveby-test-key-2024":
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                error="Unauthorized", code=401, details="Invalid or missing API key"
            ).model_dump(),
        )
    return x_api_key


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/test/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the current health status of the service. No authentication required.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {"example": {"status": "healthy"}}
            },
        }
    },
    tags=["health"],
)
async def health_check():
    """Health-check endpoint — works correctly, no auth required."""
    return {"status": "healthy"}


@app.post(
    "/widgets",
    response_model=Widget,
    status_code=201,
    summary="Create a new widget",
    description=(
        "Creates a new widget with the provided name, category, and price. "
        "Returns the created widget including its generated ID and creation timestamp."
    ),
    responses={
        201: {
            "description": "Widget created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "w-001",
                        "name": "Turbo Widget",
                        "category": "electronics",
                        "price": 29.99,
                        "created_at": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
        400: {
            "description": "Invalid request body",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "Validation error", "code": 400, "details": "price must be > 0"}
                }
            },
        },
        401: {
            "description": "Unauthorized — missing or invalid API key",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "Unauthorized", "code": 401, "details": "Invalid or missing API key"}
                }
            },
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "Internal server error", "code": 500, "details": "Database connection failed"}
                }
            },
        },
    },
    tags=["widgets"],
)
async def create_widget(widget: WidgetCreate, _key: str = Depends(verify_auth)):
    """BUG: Always raises a 500 Internal Server Error instead of creating a widget."""
    raise HTTPException(status_code=500, detail="Internal database error")


@app.get(
    "/widgets",
    response_model=WidgetList,
    summary="List all widgets",
    description="Returns a paginated list of all widgets in the system.",
    responses={
        200: {
            "description": "List of widgets",
            "content": {
                "application/json": {
                    "example": {
                        "widgets": [
                            {
                                "id": "w-001",
                                "name": "Turbo Widget",
                                "category": "electronics",
                                "price": 29.99,
                                "created_at": "2024-01-15T10:30:00Z",
                            }
                        ],
                        "total": 1,
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized — missing or invalid API key",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "Unauthorized", "code": 401, "details": "Invalid or missing API key"}
                }
            },
        },
    },
    tags=["widgets"],
)
async def list_widgets(_key: str = Depends(verify_auth)):
    """BUG: Returns a completely wrong schema instead of a widget list."""
    return {"wrong": "schema"}


@app.get(
    "/widgets/{widget_id}",
    response_model=Widget,
    summary="Get widget by ID",
    description="Retrieves a single widget by its unique identifier.",
    responses={
        200: {
            "description": "Widget found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "w-001",
                        "name": "Turbo Widget",
                        "category": "electronics",
                        "price": 29.99,
                        "created_at": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized — missing or invalid API key",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "Unauthorized", "code": 401, "details": "Invalid or missing API key"}
                }
            },
        },
        404: {
            "description": "Widget not found",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "Not found", "code": 404, "details": "Widget w-999 does not exist"}
                }
            },
        },
    },
    tags=["widgets"],
)
async def get_widget(widget_id: str, _key: str = Depends(verify_auth)):
    """BUG: Sleeps for 15 seconds before responding — causes timeouts."""
    time.sleep(15)
    return {
        "id": widget_id,
        "name": "Turbo Widget",
        "category": "electronics",
        "price": 29.99,
        "created_at": "2024-01-15T10:30:00Z",
    }


@app.delete(
    "/widgets/{widget_id}",
    status_code=204,
    summary="Delete a widget",
    description="Permanently deletes a widget by its unique identifier.",
    responses={
        204: {"description": "Widget deleted successfully"},
        401: {
            "description": "Unauthorized — missing or invalid API key",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "Unauthorized", "code": 401, "details": "Invalid or missing API key"}
                }
            },
        },
        404: {
            "description": "Widget not found",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "Not found", "code": 404, "details": "Widget w-999 does not exist"}
                }
            },
        },
    },
    tags=["widgets"],
)
async def delete_widget(widget_id: str, _key: str = Depends(verify_auth)):
    """Works correctly — but POST is broken so there's never anything to delete."""
    # In a real app this would delete from a database.
    # Since POST always 500s, there's nothing stored to delete.
    return None


# ---------------------------------------------------------------------------
# Custom OpenAPI — inject security scheme
# ---------------------------------------------------------------------------

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key passed via X-API-Key header",
        }
    }
    schema["security"] = [{"ApiKeyAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
