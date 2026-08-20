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

import * as sdk from "@ucp-js/sdk";
import { z } from "zod";

export * from "@ucp-js/sdk";

export const LineItemCreateRequestSchema =
  sdk.LineItemCreateRequestSchema.extend({
    quantity: z.number().int().gte(1),
  });
export type LineItemCreateRequest = z.infer<typeof LineItemCreateRequestSchema>;

export const LineItemUpdateRequestSchema =
  sdk.LineItemUpdateRequestSchema.extend({
    quantity: z.number().int().gte(1),
  });
export type LineItemUpdateRequest = z.infer<typeof LineItemUpdateRequestSchema>;

export const CheckoutCreateRequestSchema =
  sdk.CheckoutCreateRequestSchema.extend({
    line_items: z.array(LineItemCreateRequestSchema),
  });
export type CheckoutCreateRequest = z.infer<typeof CheckoutCreateRequestSchema>;

export const CheckoutUpdateRequestSchema =
  sdk.CheckoutUpdateRequestSchema.extend({
    line_items: z.array(LineItemUpdateRequestSchema),
  });
export type CheckoutUpdateRequest = z.infer<typeof CheckoutUpdateRequestSchema>;

export const ExtendedCheckoutCreateRequestSchema =
  sdk.ExtendedCheckoutCreateRequestSchema.extend({
    line_items: z.array(LineItemCreateRequestSchema),
  });
export type ExtendedCheckoutCreateRequest = z.infer<
  typeof ExtendedCheckoutCreateRequestSchema
>;

export const ExtendedCheckoutUpdateRequestSchema =
  sdk.ExtendedCheckoutUpdateRequestSchema.extend({
    line_items: z.array(LineItemUpdateRequestSchema),
  });
export type ExtendedCheckoutUpdateRequest = z.infer<
  typeof ExtendedCheckoutUpdateRequestSchema
>;
