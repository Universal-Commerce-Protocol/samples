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

# Node.js Server Docker Setup

This directory contains the Docker configuration for running the UCP Node.js server.

## Quick Start

To run the Node.js server:

```bash
cd samples/docker
docker-compose -f docker-compose.nodejs.yml up
```

The Node.js server will be available at `http://localhost:3000`.

## Building the Image

To build the image without starting the container:

```bash
docker-compose -f docker-compose.nodejs.yml build
```

To rebuild from scratch (no cache):

```bash
docker-compose -f docker-compose.nodejs.yml build --no-cache
```

## Accessing the Service

Once the service is running, you can access it at `http://localhost:3000`.

For detailed information on how to test and interact with the server, please refer to the [Node.js Server README](../../rest/nodejs/README.md).

## Data Persistence

The Node.js server uses a Docker volume (`nodejs-databases`) to persist SQLite databases. Data persists across container restarts.

To remove all data:

```bash
docker-compose -f docker-compose.nodejs.yml down -v
```

## Stopping the Service

To stop the service:

```bash
docker-compose -f docker-compose.nodejs.yml down
```

To stop and remove volumes (this will delete all data):

```bash
docker-compose -f docker-compose.nodejs.yml down -v
```

## Viewing Logs

To view logs from the service:

```bash
docker-compose -f docker-compose.nodejs.yml logs -f
```

## Running in Detached Mode

To run the service in the background:

```bash
docker-compose -f docker-compose.nodejs.yml up -d
```

To stop the detached service:

```bash
docker-compose -f docker-compose.nodejs.yml stop
```

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, you can change it in `docker-compose.nodejs.yml`:

```yaml
services:
  nodejs-server:
    ports:
      - "3001:3000"  # Change 3001 to your preferred port
```

### Build Failures

If builds fail, try:

1.  Clean build: `docker-compose -f docker-compose.nodejs.yml build --no-cache`
2.  Check Docker has enough resources (memory, disk space)
3.  Ensure you're in the correct directory (`samples/docker`)
4.  Make sure to specify the compose file: `docker-compose -f docker-compose.nodejs.yml build --no-cache`

### Container Health Checks

The service includes health checks. Check status:

```bash
docker-compose -f docker-compose.nodejs.yml ps
```

### Orphan Containers and Network Issues

If you see warnings about orphan containers or network errors:

1.  Stop all services and remove orphan containers:
    ```bash
    docker-compose -f docker-compose.nodejs.yml down --remove-orphans
    ```

2.  If the issue persists, remove the container manually:
    ```bash
    docker rm -f ucp-nodejs-server
    docker-compose -f docker-compose.nodejs.yml up
    ```

3.  To clean up all Docker resources (containers, networks, volumes):
    ```bash
    docker-compose -f docker-compose.nodejs.yml down -v --remove-orphans
    ```

## Development

For development, you may want to mount source code as volumes for live reloading. Modify `docker-compose.nodejs.yml` to add volume mounts:

```yaml
services:
  nodejs-server:
    volumes:
      - nodejs-databases:/app/databases
      - ../rest/nodejs/src:/app/src  # Add for live reload
```

Note: Live reloading requires additional setup and is not included in the base configuration.
