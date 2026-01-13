<!--
   Copyright 2026 UCP Authors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
-->

# UCP Docker Examples

This directory contains Docker configurations for running UCP reference
implementations. Docker provides a quick and consistent way to run the UCP servers
without needing to install Node.js, Python, or their dependencies locally.

## Prerequisites

*   [Docker](https://www.docker.com/get-started) (version 20.10 or higher)
*   [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0 or
    higher)

## Quick Start

This directory provides three Docker Compose configurations:

*   **`docker-compose.yml`** - Runs both Node.js and Python servers together
*   **`docker-compose.nodejs.yml`** - Runs only the Node.js server
*   **`docker-compose.python.yml`** - Runs only the Python server

### Running Both Servers

To start both the Node.js and Python servers:

```bash
cd samples/rest/docker
docker-compose up
```

This will:

1.  Build Docker images for both servers
2.  Initialize the Python server's database with sample data
3.  Start both servers:
    *   Node.js server on `http://localhost:3000`
    *   Python server on `http://localhost:8182`

### Running Individual Services

#### Node.js Server Only

You can run the Node.js server using the dedicated compose file:

```bash
cd samples/rest/docker
docker-compose -f docker-compose.nodejs.yml up
```

Or using the main compose file with service selection:

```bash
docker-compose up nodejs-server
```

The Node.js server will be available at `http://localhost:3000`.

#### Python Server Only

You can run the Python server using the dedicated compose file:

```bash
cd samples/rest/docker
docker-compose -f docker-compose.python.yml up
```

Or using the main compose file with service selection:

```bash
docker-compose up python-server
```

The Python server will be available at `http://localhost:8182`.

## Building Images

To build the images without starting the containers:

```bash
# Build both services
docker-compose build

# Build only Node.js
docker-compose -f docker-compose.nodejs.yml build

# Build only Python
docker-compose -f docker-compose.python.yml build
```

To rebuild images from scratch (no cache):

```bash
docker-compose build --no-cache
```

## Accessing the Services

Once the services are running, you can access them:

### Node.js Server

*   Discovery endpoint:
    ```bash
    curl http://localhost:3000/.well-known/ucp
    ```

*   Create a checkout session:
    ```bash
    curl -X POST http://localhost:3000/checkout-sessions \
      -H "Content-Type: application/json" \
      -H "UCP-Agent: profile=\"https://agent.example/profile\"" \
      -d '{
        "line_items": [{
          "item": {"id": "product_1", "title": "Test Product"},
          "quantity": 1
        }],
        "currency": "USD"
      }'
    ```

### Python Server

*   Discovery endpoint:
    ```bash
    curl http://localhost:8182/.well-known/ucp
    ```

*   Create a checkout session:
    ```bash
    curl -X POST http://localhost:8182/checkout-sessions \
      -H "Content-Type: application/json" \
      -H "UCP-Agent: profile=\"https://agent.example/profile\"" \
      -d '{
        "line_items": [{
          "item": {"id": "bouquet_roses", "title": "Red Rose"},
          "quantity": 1
        }],
        "currency": "USD",
        "buyer": {
          "full_name": "John Doe",
          "email": "john.doe@example.com"
        }
      }'
    ```

## Data Persistence

Both servers use Docker volumes to persist data:

*   **Node.js**: SQLite databases are stored in the `nodejs-databases` volume
*   **Python**: SQLite databases are stored in the `python-data` volume

Data persists across container restarts. To remove all data:

```bash
docker-compose down -v
```

## Stopping Services

To stop the services:

```bash
# Stop both services (if using main compose file)
docker-compose down

# Stop Node.js only
docker-compose -f docker-compose.nodejs.yml down

# Stop Python only
docker-compose -f docker-compose.python.yml down
```

To stop and remove volumes (this will delete all data):

```bash
docker-compose down -v
```

## Viewing Logs

To view logs from all services:

```bash
docker-compose logs -f
```

To view logs from a specific service:

```bash
docker-compose logs -f nodejs-server
docker-compose logs -f python-server
```

## Reinitializing Python Database

The Python server automatically initializes its database on first start. To
reinitialize it:

```bash
docker-compose exec python-server sh -c \
  "uv run import_csv.py \
    --products_db_path=/app/data/products.db \
    --transactions_db_path=/app/data/transactions.db \
    --data_dir=/app/test_data/flower_shop"
```

## Running in Detached Mode

To run services in the background:

```bash
docker-compose up -d
```

To stop detached services:

```bash
docker-compose stop
```

## Troubleshooting

### Port Already in Use

If ports 3000 or 8182 are already in use, you can change them in the respective
compose files:

**For Node.js** (`docker-compose.nodejs.yml` or `docker-compose.yml`):

```yaml
services:
  nodejs-server:
    ports:
      - "3001:3000"  # Change 3001 to your preferred port
```

**For Python** (`docker-compose.python.yml` or `docker-compose.yml`):

```yaml
services:
  python-server:
    ports:
      - "8183:8182"  # Change 8183 to your preferred port
```

### Database Issues

If the Python server fails to start due to database issues:

1.  Stop the services: `docker-compose down -v`
2.  Remove the volume: `docker volume rm docker_python-data`
3.  Start again: `docker-compose up`

### Build Failures

If builds fail, try:

1.  Clean build: `docker-compose build --no-cache`
2.  Check Docker has enough resources (memory, disk space)
3.  Ensure you're in the correct directory (`samples/rest/docker`)
4.  If using a specific compose file, make sure to specify it: `docker-compose -f docker-compose.nodejs.yml build --no-cache`

### Container Health Checks

Both services include health checks. Check status:

```bash
docker-compose ps
```

## Development

For development, you may want to mount source code as volumes for live
reloading. Modify the respective compose file to add volume mounts:

**For Node.js** (`docker-compose.nodejs.yml`):

```yaml
services:
  nodejs-server:
    volumes:
      - nodejs-databases:/app/databases
      - ../nodejs/src:/app/src  # Add for live reload
```

**For Python** (`docker-compose.python.yml`):

```yaml
services:
  python-server:
    volumes:
      - python-data:/app/data
      - ../python/server:/app/server  # Add for live reload
```

Note: Live reloading requires additional setup and is not included in the base
configuration.

## Additional Resources

*   [Node.js Server Documentation](../nodejs/README.md)
*   [Python Server Documentation](../python/server/README.md)
*   [UCP Documentation](https://ucp.dev)
