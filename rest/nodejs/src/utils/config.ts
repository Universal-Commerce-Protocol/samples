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
