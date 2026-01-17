from pydantic import BaseModel
import os


class Settings(BaseModel):
    ucp_version: str = "2026-01-11"
    server_base_url: str = os.getenv("SERVER_BASE_URL", "http://localhost:8183")
    simulation_secret: str = os.getenv("SIMULATION_SECRET", "letmein")


settings = Settings()