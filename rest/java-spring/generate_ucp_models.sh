#!/bin/bash
#
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
#

# Default UCP root directory assuming standard checkout structure
UCP_ROOT_DEFAULT="../../../ucp"
UCP_ROOT="${1:-$UCP_ROOT_DEFAULT}"
SPEC_SRC="$UCP_ROOT/spec"
SPEC_DEST="target/spec"

if [ ! -d "$SPEC_SRC" ]; then
  echo "Error: UCP spec directory not found at $SPEC_SRC"
  echo "Usage: $0 [path_to_ucp_root]"
  exit 1
fi

echo "Preparing specs from $SPEC_SRC into $SPEC_DEST..."

# Clean and recreate target/spec
rm -rf "$SPEC_DEST"
mkdir -p "$SPEC_DEST"

# Copy original specs
cp -r "$SPEC_SRC/"* "$SPEC_DEST/"

# Apply transformations for OpenAPI generator compatibility
# 1. Replace ucp.dev URLs with local relative paths for generator to find local files
sed -i "s/https:\/\/ucp.dev\//..\/..\//g" "$SPEC_DEST/services/shopping/rest.openapi.json"

# 2. Remove $id fields to prevent the OpenAPI 3.1 generator from using them as
# base URIs for reference resolution. This ensures local file-based resolution
# and avoids errors when specs are not yet hosted or when testing local changes.
find "$SPEC_DEST" -name "*.json" -exec sed -i '/"$id":/d' {} +

echo "Specs prepared. Running code generation..."

# Run the code generator pointing to the modified specs
mvn -f codegen.pom.xml generate-sources -Dspec.dir="$SPEC_DEST"