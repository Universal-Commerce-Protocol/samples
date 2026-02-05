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

FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY samples/rest/nodejs/package*.json ./

# Install dependencies
RUN npm install

# Copy source files
COPY samples/rest/nodejs/tsconfig.json ./
COPY samples/rest/nodejs/src ./src
COPY samples/rest/nodejs/scripts ./scripts

# Create databases directory
RUN mkdir -p databases

# Expose port
EXPOSE 3000

# Start server using tsx (runs TypeScript directly, no build step needed)
CMD ["npx", "tsx", "src/index.ts"]
