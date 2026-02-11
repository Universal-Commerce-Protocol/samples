#!/bin/bash
quicktype \
  --lang typescript-zod \
  --src-lang schema \
  --src ../../../spec/discovery/*.json \
  --src ../../../spec/schemas/shopping/*.json \
  --src ../../../spec/schemas/shopping/types/*.json \
  --src '../../../spec/schemas/shopping/ap2_mandate.json#/$defs/complete_request_with_ap2' \
  --src '../../../spec/schemas/shopping/ap2_mandate.json#/$defs/checkout_response_with_ap2' \
  --src '../../../spec/schemas/shopping/buyer_consent.json#/$defs/checkout' \
  --src '../../../spec/schemas/shopping/discount.json#/$defs/checkout' \
  --src '../../../spec/schemas/shopping/fulfillment.create_req.json#/$defs/checkout' \
  --src '../../../spec/schemas/shopping/fulfillment.update_req.json#/$defs/checkout' \
  --src '../../../spec/schemas/shopping/fulfillment_resp.json#/$defs/checkout' \
  -o src/models/spec_generated.ts
