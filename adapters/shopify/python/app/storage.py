from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class IdempotencyRecord:
    request_hash: str
    response_body: Any
    created_at: float


class InMemoryStore:
    def __init__(self) -> None:
        self.checkouts: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.idempotency: Dict[str, IdempotencyRecord] = {}

    def new_id(self, prefix: Optional[str] = None) -> str:
        if prefix:
            return f"{prefix}_{uuid.uuid4()}"
        return str(uuid.uuid4())

    def get_idempotency(self, key: str) -> Optional[IdempotencyRecord]:
        return self.idempotency.get(key)

    def put_idempotency(self, key: str, request_hash: str, response_body: Any) -> None:
        self.idempotency[key] = IdempotencyRecord(
            request_hash=request_hash,
            response_body=response_body,
            created_at=time.time(),
        )

    def idempotency_check_or_raise(
        self, key: str, payload: Any
    ) -> Tuple[Optional[Any], str]:
        """
        Returns (existing_response, request_hash).
        If key exists but payload hash differs => raise ValueError("IDEMPOTENCY_CONFLICT")
        """
        request_hash = _stable_hash(payload)
        rec = self.get_idempotency(key)
        if rec:
            if rec.request_hash != request_hash:
                raise ValueError("IDEMPOTENCY_CONFLICT")
            return rec.response_body, request_hash
        return None, request_hash


store = InMemoryStore()