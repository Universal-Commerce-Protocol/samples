from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from .routes.discovery import router as discovery_router
from .routes.catalog import router as catalog_router
from .routes.checkout import router as checkout_router
from .routes.orders import router as orders_router
from .routes.testing import router as testing_router


app = FastAPI(title="UCP Shopify Adapter (Mock)", version="0.1.0")

app.include_router(discovery_router)
app.include_router(catalog_router)
app.include_router(checkout_router)
app.include_router(orders_router)
app.include_router(testing_router)

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

def run() -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=8183, reload=True)


if __name__ == "__main__":
    run()