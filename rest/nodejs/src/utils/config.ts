// Copyright 2026 UCP Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

export const UCP_VERSION = "2026-04-08";

// RFC 9421 request-signature behaviour, sourced from the environment like
// SIMULATION_SECRET in api/testing.ts. Both default to false: signatures are
// verified when present but unsigned or invalid requests are only logged, and
// profile URLs must be HTTPS on non-private hosts. Mutable so tests can toggle
// enforcement, mirroring the Python server's config.FLAGS.
export const signatureConfig = {
  requireSignatures: process.env.REQUIRE_SIGNATURES === "true",
  allowInsecureProfileUrls: process.env.ALLOW_INSECURE_PROFILE_URLS === "true",
};
