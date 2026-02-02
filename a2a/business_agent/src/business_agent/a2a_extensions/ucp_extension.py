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

from typing import Any
from ..constants import A2A_UCP_EXTENSION_URL
from .base_extension import A2AExtensionBase

class UcpExtension(A2AExtensionBase):
    """UCP extension implementation."""

    URI: str = A2A_UCP_EXTENSION_URL

    def __init__(
        self,
        description: str = "UCP Extension",
        params: dict[str, Any] | None = None,
    ):
        """Initialize the UCP extension.

        Args:
            description: A short description of the extension.
            params: Optional parameters for the extension.

        """
        super().__init__(description, params)
