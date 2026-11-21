#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Integration tests for the MCP transport's checkout tools."""

import json
from typing import Any
import uuid

from absl.testing import absltest
import config
from exceptions import UcpError
import integration_test
from routes import mcp

PROFILE = "https://agent.example/profile"
CHECKOUT_TOOLS = [
  "create_checkout",
  "get_checkout",
  "update_checkout",
  "complete_checkout",
  "cancel_checkout",
]


class McpCheckoutTest(integration_test.IntegrationTest):
  """The checkout tools behave over MCP as the operations do over REST."""

  # Only the MCP tests run here; the inherited ones run in integration_test.
  for _inherited in [
    _n for _n in dir(integration_test.IntegrationTest) if _n.startswith("test_")
  ]:
    locals()[_inherited] = None
  del _inherited

  def _meta(self, idempotency_key: str | None = None) -> dict[str, Any]:
    meta: dict[str, Any] = {"ucp-agent": {"profile": PROFILE}}
    if idempotency_key is not None:
      meta["idempotency-key"] = idempotency_key
    return meta

  def _rpc(self, method: str, params: dict[str, Any] | None = None):
    body: dict[str, Any] = {"jsonrpc": "2.0", "id": 7, "method": method}
    if params is not None:
      body["params"] = params
    return self.client.post("/mcp", json=body)

  def _call(self, name: str, **arguments: Any):
    """Call a tool; ``meta`` defaults to a valid one with a fresh key."""
    arguments.setdefault("meta", self._meta(str(uuid.uuid4())))
    return self._rpc("tools/call", {"name": name, "arguments": arguments})

  def _ok(self, response) -> dict[str, Any]:
    """Return the UCP payload of a successful tool call."""
    self.assertEqual(response.status_code, 200, response.text)
    body = response.json()
    self.assertNotIn("error", body, response.text)
    self.assertEqual(body["id"], 7)
    result = body["result"]
    payload = result["structuredContent"]
    # The text block repeats the structured payload for clients that only
    # read ``content``.
    self.assertEqual(result["content"][0]["type"], "text")
    self.assertEqual(json.loads(result["content"][0]["text"]), payload)
    return payload

  def _rpc_error(self, response, code: int, status_code: int = 200) -> dict:
    """Return the JSON-RPC error object after checking its code."""
    self.assertEqual(response.status_code, status_code, response.text)
    body = response.json()
    self.assertNotIn("result", body, response.text)
    self.assertEqual(body["error"]["code"], code, response.text)
    return body["error"]

  def _create(self, quantity: int = 1) -> dict[str, Any]:
    return self._ok(
      self._call(
        "create_checkout",
        checkout={
          "line_items": [{"item": {"id": "rose"}, "quantity": quantity}]
        },
      )
    )

  def _rest_headers(self) -> dict[str, str]:
    return self._get_headers()

  def test_tools_list_matches_the_binding(self) -> None:
    """Every checkout tool is listed with the inputs the binding names."""
    with self.client:
      response = self._rpc("tools/list")
    self.assertEqual(response.status_code, 200)
    tools = {t["name"]: t for t in response.json()["result"]["tools"]}
    self.assertEqual(sorted(tools), sorted(CHECKOUT_TOOLS))
    required = {n: tools[n]["inputSchema"]["required"] for n in tools}
    self.assertEqual(
      required,
      {
        "create_checkout": ["meta", "checkout"],
        "get_checkout": ["meta", "id"],
        "update_checkout": ["meta", "id", "checkout"],
        "complete_checkout": ["meta", "id", "checkout"],
        "cancel_checkout": ["meta", "id"],
      },
    )
    meta = tools["create_checkout"]["inputSchema"]["properties"]["meta"]
    self.assertEqual(meta["required"], ["ucp-agent"])

  def test_create_returns_the_checkout_as_structured_content(self) -> None:
    """A created checkout comes back as the tool result."""
    with self.client:
      checkout = self._create(quantity=2)
    self.assertEqual(checkout["status"], "incomplete")
    self.assertEqual(checkout["line_items"][0]["quantity"], 2)
    self.assertEqual(checkout["ucp"]["version"], "2026-04-08")
    self.assertTrue(checkout["id"])

  def test_checkout_lifecycle(self) -> None:
    """Create, read, update and complete one checkout over MCP."""
    with self.client:
      payload = self._create_checkout_payload(
        "ignored", [("rose", "Red Rose", 1000, 1)]
      ).model_dump(mode="json", exclude_none=True)
      created = self._ok(self._call("create_checkout", checkout=payload))
      checkout_id = self.get_resource_id(created["id"])

      fetched = self._ok(self._call("get_checkout", id=checkout_id))
      self.assertEqual(fetched["id"], created["id"])

      update = dict(payload)
      update.pop("id", None)
      update["line_items"] = [{"item": {"id": "rose"}, "quantity": 2}]
      updated = self._ok(
        self._call("update_checkout", id=checkout_id, checkout=update)
      )
      self.assertEqual(updated["line_items"][0]["quantity"], 2)

      completed = self._ok(
        self._call(
          "complete_checkout",
          id=checkout_id,
          checkout=self._create_payment_payload(),
        )
      )
    self.assertEqual(completed["status"], "completed")
    self.assertTrue(completed["order"]["id"])

  def test_cancel(self) -> None:
    """A canceled checkout reports that status."""
    with self.client:
      checkout_id = self.get_resource_id(self._create()["id"])
      canceled = self._ok(self._call("cancel_checkout", id=checkout_id))
    self.assertEqual(canceled["status"], "canceled")

  def test_both_transports_serve_the_same_checkout(self) -> None:
    """A checkout made on one transport reads identically on the other."""
    with self.client:
      via_mcp = self._create()
      mcp_id = self.get_resource_id(via_mcp["id"])
      rest = self.client.get(
        f"/checkout-sessions/{mcp_id}", headers=self._rest_headers()
      )
      self.assertEqual(rest.status_code, 200, rest.text)
      self.assertEqual(
        rest.json(), self._ok(self._call("get_checkout", id=mcp_id))
      )

      created = self.client.post(
        "/checkout-sessions",
        headers=self._rest_headers(),
        json={"line_items": [{"item": {"id": "tulip"}, "quantity": 1}]},
      )
      self.assertEqual(created.status_code, 201, created.text)
      rest_id = self.get_resource_id(created.json()["id"])
      self.assertEqual(
        self._ok(self._call("get_checkout", id=rest_id)), created.json()
      )

  def test_business_outcome_is_a_result_not_an_rpc_error(self) -> None:
    """An out of stock item answers with the envelope REST would send."""
    with self.client:
      line_items = [{"item": {"id": "rose"}, "quantity": 100}]
      rest = self.client.post(
        "/checkout-sessions",
        headers=self._rest_headers(),
        json={"line_items": line_items},
      )
      self.assertEqual(rest.status_code, 400, rest.text)
      outcome = self._ok(
        self._call("create_checkout", checkout={"line_items": line_items})
      )
    self.assertEqual(outcome, rest.json())
    self.assertEqual(outcome["ucp"]["status"], "error")
    self.assertEqual(outcome["messages"][0]["code"], "OUT_OF_STOCK")

  def test_unknown_checkout_is_a_business_outcome(self) -> None:
    """Asking for a checkout that does not exist is not a transport error."""
    with self.client:
      outcome = self._ok(self._call("get_checkout", id="missing"))
    self.assertEqual(outcome["ucp"]["status"], "error")
    self.assertEqual(outcome["messages"][0]["code"], "RESOURCE_NOT_FOUND")

  def test_ucp_agent_is_required(self) -> None:
    """A call that does not identify the platform fails discovery."""
    for meta in ({}, {"ucp-agent": {}}, {"ucp-agent": "profile"}, None):
      with self.subTest(meta=meta), self.client:
        arguments: dict[str, Any] = {"checkout": {"line_items": []}}
        if meta is not None:
          arguments["meta"] = meta
        response = self._rpc(
          "tools/call", {"name": "create_checkout", "arguments": arguments}
        )
        error = self._rpc_error(response, -32001, status_code=400)
        self.assertEqual(error["data"]["code"], "invalid_profile_url")

  def test_signed_request_cannot_act_for_another_platform(self) -> None:
    """The profile in meta must be the one the signature was checked for."""
    params = {
      "name": "create_checkout",
      "arguments": {
        "meta": self._meta(),
        "checkout": {"line_items": [{"item": {"id": "rose"}, "quantity": 1}]},
      },
    }
    body = {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": params}
    other = {"UCP-Agent": 'profile="https://other.example/profile"'}
    # Signatures are verified but not enforced by default, so a dummy one is
    # enough to mark the request as signed.
    signed = {"Signature-Input": "sig1=()", "Signature": "sig1=:AA==:"}
    with self.client:
      mismatch = self.client.post("/mcp", json=body, headers=other | signed)
      error = self._rpc_error(mismatch, -32000, status_code=401)
      self.assertEqual(error["data"]["code"], "signature_invalid")

      same = {"UCP-Agent": f'profile="{PROFILE}"'}
      self._ok(self.client.post("/mcp", json=body, headers=same | signed))
      # Unsigned, the header identifies nobody and is not compared.
      self._ok(self.client.post("/mcp", json=body, headers=other))

  def test_unsigned_call_is_rejected_when_signatures_are_required(self) -> None:
    """Tool calls sit behind the same signature policy as the REST routes."""
    config.FLAGS.require_signatures = True
    try:
      with self.client:
        response = self._call("get_checkout", id="any")
    finally:
      config.FLAGS.require_signatures = False
    self.assertEqual(response.status_code, 401, response.text)
    self.assertEqual(
      response.json()["messages"][0]["code"], "signature_missing"
    )

  def test_complete_and_cancel_require_an_idempotency_key(self) -> None:
    """The binding makes the key mandatory for the two final operations."""
    with self.client:
      checkout_id = self.get_resource_id(self._create()["id"])
      calls = {
        "complete_checkout": {"checkout": self._create_payment_payload()},
        "cancel_checkout": {},
      }
      for name, arguments in calls.items():
        with self.subTest(tool=name):
          response = self._call(
            name, id=checkout_id, meta=self._meta(), **arguments
          )
          error = self._rpc_error(response, -32602)
          self.assertIn("idempotency-key", error["data"]["content"])
      # Nothing above reached the checkout.
      fetched = self._ok(self._call("get_checkout", id=checkout_id))
    self.assertEqual(fetched["status"], "incomplete")

  def test_create_and_update_work_without_an_idempotency_key(self) -> None:
    """The key stays optional where the binding does not require it."""
    with self.client:
      created = self._ok(
        self._call(
          "create_checkout",
          meta=self._meta(),
          checkout={"line_items": [{"item": {"id": "rose"}, "quantity": 1}]},
        )
      )
      updated = self._ok(
        self._call(
          "update_checkout",
          meta=self._meta(),
          id=self.get_resource_id(created["id"]),
          checkout={"line_items": [{"item": {"id": "rose"}, "quantity": 3}]},
        )
      )
    self.assertEqual(updated["line_items"][0]["quantity"], 3)

  def test_invalid_calls_are_rejected_as_invalid_params(self) -> None:
    """Unknown tools and malformed arguments never reach a handler."""
    with self.client:
      checkout_id = self.get_resource_id(self._create()["id"])
      meta = self._meta("k")
      line_items = [{"item": {"id": "rose"}, "quantity": 1}]
      cases = {
        "unknown tool": {"name": "delete_checkout", "arguments": {}},
        "no arguments": {"name": "get_checkout"},
        "no id": {"name": "get_checkout", "arguments": {"meta": meta}},
        "no checkout": {
          "name": "create_checkout",
          "arguments": {"meta": meta},
        },
        "empty checkout": {
          "name": "create_checkout",
          "arguments": {"meta": meta, "checkout": {}},
        },
        "wrong type": {
          "name": "create_checkout",
          "arguments": {
            "meta": meta,
            "checkout": {
              "line_items": [{"item": {"id": "rose"}, "quantity": "two"}]
            },
          },
        },
        "non-string idempotency key": {
          "name": "create_checkout",
          "arguments": {
            "meta": {**meta, "idempotency-key": 123},
            "checkout": {"line_items": line_items},
          },
        },
        "id inside checkout": {
          "name": "update_checkout",
          "arguments": {
            "meta": meta,
            "id": checkout_id,
            "checkout": {"id": checkout_id, "line_items": line_items},
          },
        },
      }
      for label, params in cases.items():
        with self.subTest(case=label):
          error = self._rpc_error(self._rpc("tools/call", params), -32602)
          self.assertEqual(error["data"]["code"], "INVALID_REQUEST")
      with self.subTest(case="params not an object"):
        self._rpc_error(self._rpc("tools/call", None), -32602)

  def test_idempotency_key_replays_and_conflicts(self) -> None:
    """The key deduplicates a retry and rejects a different payload."""
    with self.client:
      meta = self._meta(str(uuid.uuid4()))
      checkout = {"line_items": [{"item": {"id": "rose"}, "quantity": 1}]}
      first = self._ok(
        self._call("create_checkout", meta=meta, checkout=checkout)
      )
      again = self._ok(
        self._call("create_checkout", meta=meta, checkout=checkout)
      )
      self.assertEqual(first["id"], again["id"])

      changed = {"line_items": [{"item": {"id": "rose"}, "quantity": 2}]}
      conflict = self._call("create_checkout", meta=meta, checkout=changed)
      error = self._rpc_error(conflict, -32000, status_code=409)
    self.assertEqual(error["data"]["code"], "IDEMPOTENCY_CONFLICT")

  def test_completing_twice_is_a_business_outcome(self) -> None:
    """A checkout that is already complete answers with an error envelope."""
    with self.client:
      payload = self._create_checkout_payload(
        "ignored", [("rose", "Red Rose", 1000, 1)]
      ).model_dump(mode="json", exclude_none=True)
      created = self._ok(self._call("create_checkout", checkout=payload))
      checkout_id = self.get_resource_id(created["id"])
      payment = self._create_payment_payload()
      self._ok(
        self._call("complete_checkout", id=checkout_id, checkout=payment)
      )
      outcome = self._ok(
        self._call("complete_checkout", id=checkout_id, checkout=payment)
      )
    self.assertEqual(outcome["ucp"]["status"], "error")
    self.assertEqual(
      outcome["messages"][0]["content"],
      "Cannot complete checkout in state 'completed'",
    )

  def test_unsupported_version_fails_discovery(self) -> None:
    """A version= on the UCP-Agent header is negotiated as on REST."""
    params = {
      "name": "create_checkout",
      "arguments": {
        "meta": self._meta(),
        "checkout": {"line_items": [{"item": {"id": "rose"}, "quantity": 1}]},
      },
    }
    body = {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": params}
    header = f'profile="{PROFILE}"; version="2099-01-01"'
    with self.client:
      response = self.client.post(
        "/mcp", json=body, headers={"UCP-Agent": header}
      )
    error = self._rpc_error(response, -32001, status_code=422)
    self.assertEqual(error["data"]["code"], "VERSION_UNSUPPORTED")

  def test_declined_payment_is_a_business_outcome(self) -> None:
    """A fraud decline is a 403 on REST and still not a transport error."""
    with self.client:
      payload = self._create_checkout_payload(
        "ignored", [("rose", "Red Rose", 1000, 1)]
      ).model_dump(mode="json", exclude_none=True)
      created = self._ok(self._call("create_checkout", checkout=payload))
      payment = self._create_payment_payload()
      payment["payment"]["instruments"][0]["credential"]["token"] = (
        "fraud_token"
      )
      outcome = self._ok(
        self._call(
          "complete_checkout",
          id=self.get_resource_id(created["id"]),
          checkout=payment,
        )
      )
    self.assertEqual(outcome["ucp"]["status"], "error")
    self.assertEqual(outcome["messages"][0]["code"], "FRAUD_DETECTED")
    self.assertEqual(outcome["messages"][0]["severity"], "requires_buyer_input")

  def test_completed_checkout_reads_the_same_on_rest(self) -> None:
    """The completed checkout, order included, serialises identically."""
    with self.client:
      payload = self._create_checkout_payload(
        "ignored", [("rose", "Red Rose", 1000, 1)]
      ).model_dump(mode="json", exclude_none=True)
      created = self._ok(self._call("create_checkout", checkout=payload))
      checkout_id = self.get_resource_id(created["id"])
      self._ok(
        self._call(
          "complete_checkout",
          id=checkout_id,
          checkout=self._create_payment_payload(),
        )
      )
      rest = self.client.get(
        f"/checkout-sessions/{checkout_id}", headers=self._rest_headers()
      )
      self.assertEqual(rest.status_code, 200, rest.text)
      via_mcp = self._ok(self._call("get_checkout", id=checkout_id))
    self.assertEqual(via_mcp, rest.json())
    self.assertEqual(via_mcp["status"], "completed")

  def test_server_errors_are_internal_errors(self) -> None:
    """An unexpected failure answers -32603 without leaking its cause."""
    failures = {
      "ucp error": UcpError("database is down"),
      "bug": RuntimeError("secret detail"),
    }
    original = mcp._HANDLERS["get_checkout"]
    try:
      for label, failure in failures.items():

        async def _fail(call, service, failure=failure):
          del call, service
          raise failure

        mcp._HANDLERS["get_checkout"] = _fail
        with self.subTest(case=label), self.client:
          response = self._call("get_checkout", id="any")
          error = self._rpc_error(response, -32603, status_code=500)
          self.assertEqual(error["message"], "Internal error")
          self.assertNotIn("secret detail", response.text)
    finally:
      mcp._HANDLERS["get_checkout"] = original

  def test_json_rpc_framing(self) -> None:
    """Notifications are not run, and malformed requests are refused."""
    call = {
      "name": "create_checkout",
      "arguments": {
        "meta": self._meta(),
        "checkout": {"line_items": [{"item": {"id": "rose"}, "quantity": 5}]},
      },
    }
    with self.client:
      # Without an id this is a notification: no reply, and nothing runs.
      notification = self.client.post(
        "/mcp", json={"jsonrpc": "2.0", "method": "tools/call", "params": call}
      )
      self.assertEqual(notification.status_code, 202)
      self.assertEqual(notification.content, b"")
      # All five roses are still in stock, so the same order succeeds.
      self._ok(self._rpc("tools/call", call))

      bad_requests = {
        "no version": {"id": 1, "method": "tools/list"},
        "wrong version": {"jsonrpc": "1.0", "id": 1, "method": "tools/list"},
        "object id": {"jsonrpc": "2.0", "id": {}, "method": "tools/list"},
        "boolean id": {"jsonrpc": "2.0", "id": True, "method": "tools/list"},
        "batch": [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}],
      }
      for label, body in bad_requests.items():
        with self.subTest(case=label):
          self._rpc_error(self.client.post("/mcp", json=body), -32600)

  def test_discovery_advertises_the_mcp_endpoint(self) -> None:
    """The profile lists the MCP service next to REST."""
    with self.client:
      profile = self.client.get("/.well-known/ucp").json()
    services = profile["ucp"]["services"]["dev.ucp.shopping"]
    mcp = [s for s in services if s["transport"] == "mcp"]
    self.assertLen(mcp, 1)
    self.assertTrue(mcp[0]["endpoint"].endswith("/mcp"))
    self.assertEqual(
      mcp[0]["schema"],
      "https://ucp.dev/2026-04-08/services/shopping/mcp.openrpc.json",
    )


if __name__ == "__main__":
  absltest.main()
