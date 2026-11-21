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

"""Catalog routes for the UCP server."""

from typing import Annotated, Any

import dependencies
from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from services.catalog_service import CatalogService
from ucp_sdk.models.schemas.shopping import catalog_lookup
from ucp_sdk.models.schemas.shopping import catalog_search

router = APIRouter()


def _encode(response: Any) -> dict[str, Any]:
  return jsonable_encoder(response, by_alias=True, exclude_none=True)


@router.post(
  "/catalog/search",
  response_model=dict[str, Any],
  operation_id="search_catalog",
)
async def search_catalog(
  search: Annotated[catalog_search.SearchRequest, Body(...)],
  common_headers: Annotated[
    dependencies.CommonHeaders, Depends(dependencies.common_headers)
  ],
  catalog_service: Annotated[
    CatalogService, Depends(dependencies.get_catalog_service)
  ],
) -> dict[str, Any]:
  """Search for products."""
  del common_headers  # Unused
  return _encode(await catalog_service.search(search))


@router.post(
  "/catalog/lookup",
  response_model=dict[str, Any],
  operation_id="lookup_catalog",
)
async def lookup_catalog(
  lookup: Annotated[catalog_lookup.LookupRequest, Body(...)],
  common_headers: Annotated[
    dependencies.CommonHeaders, Depends(dependencies.common_headers)
  ],
  catalog_service: Annotated[
    CatalogService, Depends(dependencies.get_catalog_service)
  ],
) -> dict[str, Any]:
  """Look up products by identifier."""
  del common_headers  # Unused
  return _encode(await catalog_service.lookup(lookup))


@router.post(
  "/catalog/product",
  response_model=dict[str, Any],
  operation_id="get_product",
)
async def get_product(
  product: Annotated[catalog_lookup.GetProductRequest, Body(...)],
  common_headers: Annotated[
    dependencies.CommonHeaders, Depends(dependencies.common_headers)
  ],
  catalog_service: Annotated[
    CatalogService, Depends(dependencies.get_catalog_service)
  ],
) -> dict[str, Any]:
  """Get one product by identifier."""
  del common_headers  # Unused
  return _encode(await catalog_service.get_product(product))
