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

# Python Server Docker Setup

This directory contains the Docker configuration for running the UCP Python server.

## Quick Start

To run the Python server:

```bash
cd samples/docker/python
docker-compose up
```

The Python server will be available at `http://localhost:8182`.

## Building the Image

To build the image without starting the container:

```bash
docker-compose build
```

To rebuild from scratch (no cache):

```bash
docker-compose build --no-cache
```

## Accessing the Service

Once the service is running, you can access it at `http://localhost:8182`.

For detailed information on how to test and interact with the server, please refer to the [Python Server README](../../rest/python/server/README.md).

## Data Persistence

The Python server uses a Docker volume (`python-data`) to persist SQLite databases. Data persists across container restarts.

To remove all data:

```bash
docker-compose down -v
```

## Stopping the Service

To stop the service:

```bash
docker-compose down
```

To stop and remove volumes (this will delete all data):

```bash
docker-compose down -v
```

## Viewing Logs

To view logs from the service:

```bash
docker-compose logs -f
```

## Running in Detached Mode

To run the service in the background:

```bash
docker-compose up -d
```

To stop the detached service:

```bash
docker-compose stop
```

## Troubleshooting

### Port Already in Use

If port 8182 is already in use, you can change it in `docker-compose.yml`:

```yaml
services:
  python-server:
    ports:
      - "8183:8182"  # Change 8183 to your preferred port
```

### Database Issues

If the Python server fails to start due to database issues:

1.  Stop the service: `docker-compose down -v`
2.  If the volume still exists, remove it manually:
    ```bash
    docker volume ls | grep python-data
    docker volume rm <volume-name>
    ```
3.  Start again: `docker-compose up`

### Build Failures

If builds fail, try:

1.  Clean build: `docker-compose build --no-cache`
2.  Check Docker has enough resources (memory, disk space)
3.  Ensure you're in the correct directory (`samples/docker/python`)

### Container Health Checks

The service includes health checks. Check status:

```bash
docker-compose ps
```

### Orphan Containers and Network Issues

If you see warnings about orphan containers or network errors:

1.  Stop all services and remove orphan containers:
    ```bash
    docker-compose down --remove-orphans
    ```

2.  If the issue persists, remove the container manually:
    ```bash
    docker rm -f ucp-python-server
    docker-compose up
    ```

3.  To clean up all Docker resources (containers, networks, volumes):
    ```bash
    docker-compose down -v --remove-orphans
    ```

## Development

For development, you may want to mount source code as volumes for live reloading. Modify `docker-compose.yml` to add volume mounts:

```yaml
services:
  python-server:
    volumes:
      - python-data:/app/data
      - ../rest/python/server:/app/server  # Add for live reload
```

Note: Live reloading requires additional setup and is not included in the base configuration.
