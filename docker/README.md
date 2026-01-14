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

This directory provides two Docker Compose configurations:

*   **`docker-compose.nodejs.yml`** - Runs only the Node.js server
*   **`docker-compose.python.yml`** - Runs only the Python server

### Running Individual Services

#### Node.js Server Only

You can run the Node.js server using the dedicated compose file:

```bash
cd samples/docker
docker-compose -f docker-compose.nodejs.yml up
```

The Node.js server will be available at `http://localhost:3000`.

#### Python Server Only

You can run the Python server using the dedicated compose file:

```bash
cd samples/docker
docker-compose -f docker-compose.python.yml up
```

The Python server will be available at `http://localhost:8182`.

### Running Both Servers

To start both the Node.js and Python servers, you need to run them in separate terminals:

**Terminal 1 - Node.js Server:**
```bash
cd samples/docker
docker-compose -f docker-compose.nodejs.yml up
```

**Terminal 2 - Python Server:**
```bash
cd samples/docker
docker-compose -f docker-compose.python.yml up
```

This will:

1.  Build Docker images for both servers
2.  Initialize the Python server's database with sample data
3.  Start both servers:
    *   Node.js server on `http://localhost:3000`
    *   Python server on `http://localhost:8182`

## Building Images

To build the images without starting the containers:

```bash
# Build Node.js server
docker-compose -f docker-compose.nodejs.yml build

# Build Python server
docker-compose -f docker-compose.python.yml build
```

To rebuild images from scratch (no cache):

```bash
# Rebuild Node.js server
docker-compose -f docker-compose.nodejs.yml build --no-cache

# Rebuild Python server
docker-compose -f docker-compose.python.yml build --no-cache
```

## Accessing the Services

Once the services are running, you can access them. For detailed information on how to test and interact with each server, please refer to their respective documentation:

### Node.js Server

*   **Documentation**: [Node.js Server README](../rest/nodejs/README.md)
*   Available at `http://localhost:3000`

### Python Server

*   **Documentation**: [Python Server README](../rest/python/server/README.md)
*   Available at `http://localhost:8182`

## Data Persistence

Both servers use Docker volumes to persist data:

*   **Node.js**: SQLite databases are stored in the `nodejs-databases` volume
*   **Python**: SQLite databases are stored in the `python-data` volume

Data persists across container restarts. To remove all data:

```bash
# Remove Node.js data
docker-compose -f docker-compose.nodejs.yml down -v

# Remove Python data
docker-compose -f docker-compose.python.yml down -v
```

## Stopping Services

To stop the services:

```bash
# Stop Node.js
docker-compose -f docker-compose.nodejs.yml down

# Stop Python
docker-compose -f docker-compose.python.yml down
```

To stop and remove volumes (this will delete all data):

```bash
# Stop Node.js and remove volumes
docker-compose -f docker-compose.nodejs.yml down -v

# Stop Python and remove volumes
docker-compose -f docker-compose.python.yml down -v
```

## Viewing Logs

To view logs from a specific service:

```bash
# Node.js server logs
docker-compose -f docker-compose.nodejs.yml logs -f

# Python server logs
docker-compose -f docker-compose.python.yml logs -f
```

## Reinitializing Python Database

The Python server automatically initializes its database on first start. To
reinitialize it:

```bash
docker-compose -f docker-compose.python.yml exec python-server sh -c \
  "uv run import_csv.py \
    --products_db_path=/app/data/products.db \
    --transactions_db_path=/app/data/transactions.db \
    --data_dir=/app/test_data/flower_shop"
```

## Running in Detached Mode

To run services in the background:

```bash
# Run Node.js server in background
docker-compose -f docker-compose.nodejs.yml up -d

# Run Python server in background
docker-compose -f docker-compose.python.yml up -d
```

To stop detached services:

```bash
# Stop Node.js server
docker-compose -f docker-compose.nodejs.yml stop

# Stop Python server
docker-compose -f docker-compose.python.yml stop
```

## Troubleshooting

### Port Already in Use

If ports 3000 or 8182 are already in use, you can change them in the respective
compose files:

**For Node.js** (`docker-compose.nodejs.yml`):

```yaml
services:
  nodejs-server:
    ports:
      - "3001:3000"  # Change 3001 to your preferred port
```

**For Python** (`docker-compose.python.yml`):

```yaml
services:
  python-server:
    ports:
      - "8183:8182"  # Change 8183 to your preferred port
```

### Database Issues

If the Python server fails to start due to database issues:

1.  Stop the service: `docker-compose -f docker-compose.python.yml down -v`
2.  Remove the volume: `docker volume rm samples_docker_python-data`
3.  Start again: `docker-compose -f docker-compose.python.yml up`

### Build Failures

If builds fail, try:

1.  Clean build: `docker-compose -f docker-compose.nodejs.yml build --no-cache` or `docker-compose -f docker-compose.python.yml build --no-cache`
2.  Check Docker has enough resources (memory, disk space)
3.  Ensure you're in the correct directory (`samples/docker`)
4.  Make sure to specify the compose file: `docker-compose -f docker-compose.nodejs.yml build --no-cache` or `docker-compose -f docker-compose.python.yml build --no-cache`

### Container Health Checks

Both services include health checks. Check status:

```bash
# Check Node.js server status
docker-compose -f docker-compose.nodejs.yml ps

# Check Python server status
docker-compose -f docker-compose.python.yml ps
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
      - ../rest/nodejs/src:/app/src  # Add for live reload
```

**For Python** (`docker-compose.python.yml`):

```yaml
services:
  python-server:
    volumes:
      - python-data:/app/data
      - ../rest/python/server:/app/server  # Add for live reload
```

Note: Live reloading requires additional setup and is not included in the base
configuration.

## Additional Resources

*   [Node.js Server Documentation](../rest/nodejs/README.md)
*   [Python Server Documentation](../rest/python/server/README.md)
*   [UCP Documentation](https://ucp.dev)
