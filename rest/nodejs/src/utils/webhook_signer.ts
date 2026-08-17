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

// The business's webhook-signing identity.
//
// Order-event webhooks MUST be signed by the business (order.md, Webhook
// Signature Verification) with a key the business publishes in its profile's
// signing_keys[] so platforms can verify the deliveries. This module owns
// that identity:
//
// * WEBHOOK_SIGNING_KEY loads an operator-provided PEM private key (EC P-256
//   for ES256, or Ed25519). When unset, an ephemeral demo key is generated
//   at startup -- the server signs correctly out of the box and no
//   private-key file ever lives in the repository.
// * The kid is the RFC 7638 JWK thumbprint of the public key, so the same
//   key always republishes under the same identifier across restarts.

import crypto, { type KeyObject } from "node:crypto";
import fs from "node:fs";

import { webhookConfig } from "./config";
import { jwkFromPublicKey, type Jwk } from "./signature";

// The lazily-created (private key, kid) signing identity for this process.
let signer: { privateKey: KeyObject; kid: string } | null = null;

// Returns the `{ privateKey, kid }` this business signs webhooks with.
//
// Loaded once per process: from the WEBHOOK_SIGNING_KEY PEM when configured,
// otherwise a fresh ephemeral ES256 demo key. A configured path that cannot
// be read or holds an unsupported key type fails loudly -- silently signing
// with a different identity than the operator configured would be wrong.
export function signingKey(): { privateKey: KeyObject; kid: string } {
  if (signer === null) {
    const path = webhookConfig.signingKeyPath;
    let privateKey: KeyObject;
    if (path) {
      privateKey = crypto.createPrivateKey(fs.readFileSync(path));
      const keyType = privateKey.asymmetricKeyType;
      if (keyType === "ec") {
        const curve = privateKey.asymmetricKeyDetails?.namedCurve;
        if (curve !== "prime256v1") {
          throw new Error(
            "WEBHOOK_SIGNING_KEY must be EC P-256 (ES256) or Ed25519; " +
              `got EC curve ${curve}`
          );
        }
      } else if (keyType !== "ed25519") {
        throw new Error(
          "WEBHOOK_SIGNING_KEY must be EC P-256 (ES256) or Ed25519; " +
            `got ${keyType}`
        );
      }
    } else {
      privateKey = crypto.generateKeyPairSync("ec", {
        namedCurve: "P-256",
      }).privateKey;
    }
    const publicKey = crypto.createPublicKey(privateKey);
    signer = { privateKey, kid: thumbprintKid(publicKey) };
  }
  return signer;
}

// Returns the public JWK to publish in the profile's signing_keys[].
export function publicJwk(): Jwk {
  const { privateKey, kid } = signingKey();
  return jwkFromPublicKey(crypto.createPublicKey(privateKey), kid);
}

// Discards the cached signing identity (used by tests).
export function resetSigner(): void {
  signer = null;
}

// Derives the RFC 7638 JWK thumbprint (base64url SHA-256) as the kid.
//
// The thumbprint hashes only the REQUIRED public members in lexicographic
// order with no whitespace, so it is deterministic for a given key.
function thumbprintKid(publicKey: KeyObject): string {
  const jwk = jwkFromPublicKey(publicKey, "");
  const members: Record<string, unknown> =
    jwk.kty === "OKP"
      ? { crv: jwk.crv, kty: jwk.kty, x: jwk.x }
      : { crv: jwk.crv, kty: jwk.kty, x: jwk.x, y: jwk.y };
  // An array replacer serializes exactly these members, in this order
  // (lexicographic), with no whitespace -- RFC 7638's canonical form.
  const canonical = JSON.stringify(members, Object.keys(members).sort());
  return crypto
    .createHash("sha256")
    .update(canonical, "utf-8")
    .digest("base64url");
}
