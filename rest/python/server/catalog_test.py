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

"""Integration tests for the catalog search and lookup capabilities."""

from typing import Any

from absl.testing import absltest
import integration_test
from services import catalog_service
from ucp_sdk.models.schemas.shopping import catalog_lookup
from ucp_sdk.models.schemas.shopping import catalog_search


class CatalogTest(integration_test.IntegrationTest):
  """Search, lookup and get product over REST."""

  # Only the catalog tests run here; the inherited ones run in
  # integration_test.
  for _inherited in [
    _n for _n in dir(integration_test.IntegrationTest) if _n.startswith("test_")
  ]:
    locals()[_inherited] = None
  del _inherited

  def _post(self, path: str, body: dict[str, Any], status: int = 200):
    response = self.client.post(path, headers=self._get_headers(), json=body)
    self.assertEqual(response.status_code, status, response.text)
    return response.json()

  def test_search_matches_the_title(self) -> None:
    """A query returns the products whose title contains every term."""
    with self.client:
      body = self._post("/catalog/search", {"query": "red ROSE"})
    catalog_search.SearchResponse.model_validate(body)
    self.assertEqual([p["id"] for p in body["products"]], ["rose"])
    self.assertIn(
      catalog_service.SEARCH_CAPABILITY, body["ucp"]["capabilities"]
    )
    product = body["products"][0]
    self.assertEqual(
      product["price_range"]["min"], {"amount": 1000, "currency": "USD"}
    )
    # The variant id is the id checkout takes as a line item.
    self.assertEqual(product["variants"][0]["id"], "rose")
    self.assertTrue(product["variants"][0]["availability"]["available"])

  def test_search_without_matches_is_empty(self) -> None:
    """No match is an empty list, not an error."""
    with self.client:
      body = self._post("/catalog/search", {"query": "cactus"})
      # A wildcard in the query is matched as text.
      wildcard = self._post("/catalog/search", {"query": "%"})
    self.assertEqual(body["products"], [])
    self.assertNotIn("messages", body)
    self.assertEqual(wildcard["products"], [])

  def test_search_needs_an_input(self) -> None:
    """A search with neither a query nor a filter is rejected."""
    with self.client:
      requests = (
        {},
        {"query": "  "},
        {"filters": {}},
        {"filters": {"categories": [], "price": {}}},
      )
      for request in requests:
        with self.subTest(request=request):
          body = self._post("/catalog/search", request, status=400)
          self.assertEqual(body["ucp"]["status"], "error")

  def test_search_filters_by_price(self) -> None:
    """A filter alone browses the catalog."""
    with self.client:
      body = self._post("/catalog/search", {"filters": {"price": {"max": 900}}})
      none = self._post(
        "/catalog/search", {"filters": {"categories": ["Plants"]}}
      )
    self.assertEqual([p["id"] for p in body["products"]], ["tulip"])
    self.assertEqual(none["products"], [])

  def test_search_pages_with_a_cursor(self) -> None:
    """The cursor of one page fetches the next."""
    request = {"filters": {"price": {"min": 0}}, "pagination": {"limit": 1}}
    with self.client:
      first = self._post("/catalog/search", request)
      self.assertTrue(first["pagination"]["has_next_page"])
      self.assertEqual(first["pagination"]["total_count"], 2)
      request["pagination"]["cursor"] = first["pagination"]["cursor"]
      second = self._post("/catalog/search", request)
      for cursor in (
        "not a cursor",
        "LTE=",
        "MTAwMDAwMDAwMDAwMDAwMDAwMDAwMDAw",
      ):
        request["pagination"]["cursor"] = cursor
        self._post("/catalog/search", request, status=400)
    self.assertFalse(second["pagination"]["has_next_page"])
    self.assertNotIn("cursor", second["pagination"])
    ids = [first["products"][0]["id"], second["products"][0]["id"]]
    self.assertEqual(sorted(ids), ["rose", "tulip"])

  def test_lookup_returns_each_product_once(self) -> None:
    """Repeated ids are deduplicated and unknown ones are reported."""
    with self.client:
      body = self._post(
        "/catalog/lookup", {"ids": ["rose", "rose", "missing", "tulip"]}
      )
    catalog_lookup.LookupResponse.model_validate(body)
    self.assertEqual([p["id"] for p in body["products"]], ["rose", "tulip"])
    self.assertEqual(
      body["products"][0]["variants"][0]["inputs"],
      [{"id": "rose", "match": "exact"}],
    )
    self.assertLen(body["messages"], 1)
    message = body["messages"][0]
    self.assertEqual(message["type"], "info")
    self.assertEqual(message["code"], "not_found")
    self.assertEqual(message["content"], "missing")

  def test_lookup_applies_filters_after_resolution(self) -> None:
    """A product outside the price filter is left out."""
    with self.client:
      body = self._post(
        "/catalog/lookup",
        {"ids": ["rose", "tulip"], "filters": {"price": {"max": 900}}},
      )
      detail = self._post(
        "/catalog/product", {"id": "rose", "filters": {"price": {"max": 900}}}
      )
    self.assertEqual([p["id"] for p in body["products"]], ["tulip"])
    # The rose was found and filtered out, so it is not reported missing.
    self.assertNotIn("messages", body)
    self.assertEqual(detail["ucp"]["status"], "error")

  def test_lookup_rejects_an_oversized_batch(self) -> None:
    """More identifiers than the limit is a 400 request_too_large."""
    ids = [f"id_{n}" for n in range(catalog_service.MAX_LOOKUP_IDS + 1)]
    with self.client:
      body = self._post("/catalog/lookup", {"ids": ids}, status=400)
      self._post("/catalog/lookup", {"ids": ids[:-1]})
    self.assertEqual(body["messages"][0]["code"], "request_too_large")
    self.assertEqual(body["messages"][0]["severity"], "recoverable")

  def test_get_product(self) -> None:
    """A known id returns the product with its variant."""
    with self.client:
      body = self._post("/catalog/product", {"id": "tulip"})
    catalog_lookup.GetProductResponse.model_validate(body)
    self.assertEqual(body["product"]["id"], "tulip")
    self.assertEqual(body["product"]["variants"][0]["id"], "tulip")

  def test_get_product_not_found_is_an_outcome(self) -> None:
    """An unknown id answers 200 with an error in the envelope."""
    with self.client:
      body = self._post("/catalog/product", {"id": "missing"})
    self.assertEqual(body["ucp"]["status"], "error")
    self.assertEqual(body["messages"][0]["code"], "not_found")
    self.assertNotIn("product", body)

  def test_discovery_advertises_the_catalog(self) -> None:
    """Both catalog capabilities are in the discovery profile."""
    with self.client:
      profile = self.client.get("/.well-known/ucp").json()
    capabilities = profile["ucp"]["capabilities"]
    self.assertIn(catalog_service.SEARCH_CAPABILITY, capabilities)
    self.assertIn(catalog_service.LOOKUP_CAPABILITY, capabilities)


if __name__ == "__main__":
  absltest.main()
