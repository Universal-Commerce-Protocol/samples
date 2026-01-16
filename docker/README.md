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

## Available Services

This directory provides two Docker Compose configurations:

*   **`nodejs/docker-compose.yml`** - Runs the Node.js server
*   **`python/docker-compose.yml`** - Runs the Python server

For detailed instructions on how to use each service, please refer to their respective documentation:

*   [Node.js Docker Setup](./nodejs/README.md)
*   [Python Docker Setup](./python/README.md)

## Additional Resources

*   [Node.js Server Documentation](../rest/nodejs/README.md)
*   [Python Server Documentation](../rest/python/server/README.md)
*   [UCP Documentation](https://ucp.dev)
