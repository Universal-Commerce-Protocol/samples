from __future__ import annotations

from fastapi import APIRouter
from ..config import settings

router = APIRouter()


@router.get("/.well-known/ucp")
async def discovery_profile() -> dict:
    return {
        "ucp": {
            "version": settings.ucp_version,
            "services": {
                "dev.ucp.shopping": {
                    "version": settings.ucp_version,
                    "spec": "https://ucp.dev/specs/shopping",
                    "rest": {
                        "schema": None,
                        "endpoint": f"{settings.server_base_url}/",
                    },
                    "mcp": None,
                    "a2a": None,
                }
            },
        }
    }