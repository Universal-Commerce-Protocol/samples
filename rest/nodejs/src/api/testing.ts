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

import { ResourceNotFoundError, ucpErrorResponse } from "../utils/ucp_error";
import { type IdParamContext } from "../utils/validation";
import { CheckoutService } from "./checkout";

export class TestingService {
  constructor(private readonly checkoutService: CheckoutService) {}

  shipOrder = async (c: IdParamContext) => {
    const secret = c.req.header("Simulation-Secret");
    const expectedSecret =
      process.env.SIMULATION_SECRET || "super-secret-sim-key";

    if (secret !== expectedSecret) {
      return c.json({ detail: "Invalid Simulation Secret" }, 403);
    }

    const { id } = c.req.valid("param");
    try {
      await this.checkoutService.shipOrder(id, new URL(c.req.url).origin);
      return c.json({ status: "shipped" }, 200);
    } catch (e: any) {
      if (e.message === "Order not found") {
        // The Python reference answers this with the UCP error envelope
        // (services/checkout_service.py ship_order raises
        // ResourceNotFoundError -> server.py ucp_exception_handler).
        return ucpErrorResponse(
          c,
          new ResourceNotFoundError("Order not found")
        );
      }
      return c.json({ detail: e.message }, 500);
    }
  };
}
