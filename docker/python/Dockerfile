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

FROM python:3.11-slim

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy SDK first (needed by server)
COPY sdk/python /app/sdk/python

# Copy server files
COPY samples/rest/python/server /app/server

# Copy test data
COPY samples/rest/python/test_data /app/test_data

WORKDIR /app/server

# Update pyproject.toml to use the copied SDK path
RUN python3 -c "import re; content = open('pyproject.toml').read(); content = re.sub(r'path = \"\.\.\/\.\.\/\.\.\/\.\.\/sdk\/python\/\"', 'path = \"/app/sdk/python/\"', content); open('pyproject.toml', 'w').write(content)"

# Install dependencies using uv
RUN uv sync

# Create data directory for databases
RUN mkdir -p /app/data

# Expose port
EXPOSE 8182

# Default command: initialize database and start server
# Users can override this to run different commands
CMD ["sh", "-c", "uv run import_csv.py --products_db_path=/app/data/products.db --transactions_db_path=/app/data/transactions.db --data_dir=/app/test_data/flower_shop && uv run server.py --products_db_path=/app/data/products.db --transactions_db_path=/app/data/transactions.db --port=8182"]
