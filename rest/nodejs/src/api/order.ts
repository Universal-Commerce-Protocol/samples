import { type Context } from "hono";
import { getOrder, logRequest, saveOrder } from "../data";
import { type Order } from "../models";

/**
 * Service for managing orders.
 */
export class OrderService {
  getOrder = async (c: Context) => {
    const id = c.req.param("id");

    // Log Request
    logRequest("GET", `/orders/${id}`, undefined, {});

    const order = getOrder(id);
    if (!order) {
      return c.json({ error: "Order not found" }, 404);
    }
    return c.json(order, 200);
  };

  updateOrder = async (c: Context) => {
    const id = c.req.param("id");
    const updateRequest = await c.req.json<Order>();

    // Log Request
    logRequest(
      "PUT",
      `/orders/${id}`,
      updateRequest.checkout_id,
      updateRequest,
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
