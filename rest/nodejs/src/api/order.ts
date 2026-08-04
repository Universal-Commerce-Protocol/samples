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

import { getOrder, logRequest, saveOrder } from "../data";
import { type Order } from "../models";
import { type IdParamContext } from "../utils/validation";

/**
 * Service for managing orders.
 */
export class OrderService {
  getOrder = async (c: IdParamContext) => {
    const { id } = c.req.valid("param");

    // Log Request
    logRequest("GET", `/orders/${id}`, undefined, {});

    const order = getOrder(id);
    if (!order) {
      return c.json({ error: "Order not found" }, 404);
    }
    return c.json(order, 200);
  };

  updateOrder = async (c: IdParamContext) => {
    const { id } = c.req.valid("param");
    const updateRequest = await c.req.json<Order>();

    // Log Request
    logRequest(
      "PUT",
      `/orders/${id}`,
      updateRequest.checkout_id,
      updateRequest
    );

    const existing = getOrder(id);
    if (!existing) {
      return c.json({ error: "Order not found" }, 404);
    }

    // Ensure ID matches
    updateRequest.id = id;

    saveOrder(id, updateRequest);

    return c.json(updateRequest, 200);
  };
}
