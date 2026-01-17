# Copyright 2026 UCP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""UCP."""

from pathlib import Path
from datetime import datetime
import json
from a2a.types import InternalError
from a2a.utils.errors import ServerError
import httpx
from ucp_sdk.models.schemas.capability import Response as UcpMetadataCapability
from ucp_sdk.models.schemas.ucp import ResponseCheckout as UcpMetadata


class ProfileResolver:
    """Resolve a UCP profile to a UCP metadata object."""

    def __init__(self):
        """Initialize the profile resolver."""
        self.profiles = {}
        self.httpx_client = httpx.Client()
        self._load_merchant_profile()

    def _load_merchant_profile(self) -> UcpMetadata:
        """Load the merchant profile from a JSON file.

        Returns:
            UcpMetadata: The loaded merchant profile.

        """
        base_path = Path(__file__).parent
        ucp_path = base_path / "data" / "ucp.json"
        with ucp_path.open() as f:
            self.merchant_profile = json.load(f)
        return self.merchant_profile

    def _fetch_profile(self, client_profile_url: str) -> dict:
        """Fetch a profile from a URL.

        Args:
            client_profile_url: The URL of the profile to fetch.

        Returns:
            dict: The fetched profile object.

        """
        response = self.httpx_client.get(client_profile_url)
        response.raise_for_status()
        return response.json()

    def resolve_profile(self, client_profile_url: str) -> dict:
        """Resolve a profile url to a UCP profile object.

        Args:
            client_profile_url: The URL of the profile to resolve.

        Returns:
            dict: The resolved profile object.

        Raises:
            ValueError: If the profile version is missing.
            ServerError: If the version is not supported.

        """
        if client_profile_url in self.profiles:
            return self.profiles[client_profile_url]

        profile = self._fetch_profile(client_profile_url)

        client_version = profile.get("ucp").get("version")
        if not client_version:
            raise ValueError("Profile version is missing")

        merchant_version = self.merchant_profile.get("ucp").get("version")

        client_version = datetime.strptime(client_version, "%Y-%m-%d").date()
        merchant_version = datetime.strptime(
            merchant_version, "%Y-%m-%d"
        ).date()

        if client_version > merchant_version:
            raise ServerError(
                error=InternalError(
                    message=(
                        f"Version {client_version} is not supported. "
                        f"This merchant implements version {merchant_version}."
                    ),
                    data={
                        "code": "VERSION_UNSUPPORTED",
                        "severity": "critical",
                    },
                )
            )

        self.profiles[client_profile_url] = profile
        return profile

    def get_ucp_metadata(self, client_profile_metadata: dict) -> UcpMetadata:
        """Create a UCP metadata object based on common capabilities.

        Args:
            client_profile_metadata: The client profile metadata object.

        Returns:
            UcpMetadata: The created UCP metadata object.

        """
        client_capabilities: list[UcpMetadataCapability] = [
            UcpMetadataCapability(**c)
            for c in client_profile_metadata.get("ucp").get("capabilities", [])
        ]
        merchant_capabilities: list[UcpMetadataCapability] = [
            UcpMetadataCapability(**c)
            for c in self.merchant_profile.get("ucp").get("capabilities", [])
        ]

        client_capabilities_set = {
            (capability.name, capability.version.root)
            for capability in client_capabilities
        }

        common_capabilites = [
            merchant_capability
            for merchant_capability in merchant_capabilities
            if (merchant_capability.name, merchant_capability.version.root)
            in client_capabilities_set
        ]

        return UcpMetadata(
            version=self.merchant_profile.get("ucp").get("version"),
            capabilities=common_capabilites,
        )
