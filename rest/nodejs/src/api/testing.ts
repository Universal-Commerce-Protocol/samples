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
      await this.checkoutService.shipOrder(id);
      return c.json({ status: "shipped" }, 200);
    } catch (e: any) {
      if (e.message === "Order not found") {
        return c.json({ detail: "Order not found" }, 404);
      }
      return c.json({ detail: e.message }, 500);
    }
  };
}
