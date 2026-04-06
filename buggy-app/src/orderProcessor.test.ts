import { OrderProcessor } from "./orderProcessor";

function createProcessor(): OrderProcessor {
  const op = new OrderProcessor();
  op.addProduct({ id: "LAPTOP", name: "Laptop Pro", price: 999.99, stock: 10 });
  op.addProduct({ id: "MOUSE", name: "Wireless Mouse", price: 29.99, stock: 50 });
  op.addProduct({ id: "KB", name: "Mechanical Keyboard", price: 149.99, stock: 25 });
  return op;
}

describe("OrderProcessor", () => {
  describe("basic order without discount", () => {
    it("should calculate correct subtotal for multiple items", () => {
      const op = createProcessor();
      const order = op.processOrder(
        [
          { productId: "LAPTOP", quantity: 1 },
          { productId: "MOUSE", quantity: 2 },
        ],
        0,
        0.08,
      );
      expect(order.subtotal).toBeCloseTo(1059.97, 2);
    });

    it("should have zero discount when none is applied", () => {
      const op = createProcessor();
      const order = op.processOrder(
        [{ productId: "LAPTOP", quantity: 1 }],
        0,
        0.08,
      );
      expect(order.discountAmount).toBeCloseTo(0, 2);
    });

    it("should calculate correct tax at 8%", () => {
      const op = createProcessor();
      const order = op.processOrder(
        [
          { productId: "LAPTOP", quantity: 1 },
          { productId: "MOUSE", quantity: 2 },
        ],
        0,
        0.08,
      );
      expect(order.taxAmount).toBeCloseTo(84.80, 2);
    });

    it("should calculate correct total (subtotal + tax)", () => {
      const op = createProcessor();
      const order = op.processOrder(
        [
          { productId: "LAPTOP", quantity: 1 },
          { productId: "MOUSE", quantity: 2 },
        ],
        0,
        0.08,
      );
      expect(order.total).toBeCloseTo(1144.77, 2);
    });
  });

  describe("order with 10% discount", () => {
    it("should calculate correct discount amount", () => {
      const op = createProcessor();
      const order = op.processOrder(
        [{ productId: "KB", quantity: 1 }],
        10,
        0.08,
      );
      expect(order.discountAmount).toBeCloseTo(15.00, 2);
    });

    it("should apply discount before tax and calculate correct total", () => {
      const op = createProcessor();
      const order = op.processOrder(
        [{ productId: "KB", quantity: 1 }],
        10,
        0.08,
      );
      // KB = $149.99, 10% off = $15.00, after discount = $134.99
      // Tax on $134.99 at 8% = $10.80, total = $145.79
      expect(order.total).toBeCloseTo(145.79, 2);
    });
  });

  describe("inventory management", () => {
    it("should decrease stock by the quantity ordered", () => {
      const op = createProcessor();
      op.processOrder([{ productId: "MOUSE", quantity: 5 }], 0, 0);
      const mouse = op.getProduct("MOUSE");
      expect(mouse!.stock).toBe(45);
    });

    it("should not affect stock of products not in the order", () => {
      const op = createProcessor();
      op.processOrder([{ productId: "MOUSE", quantity: 5 }], 0, 0);
      const laptop = op.getProduct("LAPTOP");
      expect(laptop!.stock).toBe(10);
    });
  });

  describe("error handling", () => {
    it("should throw error for insufficient stock", () => {
      const op = createProcessor();
      expect(() => {
        op.processOrder([{ productId: "LAPTOP", quantity: 999 }], 0, 0);
      }).toThrow("Insufficient stock");
    });

    it("should throw error for unknown product", () => {
      const op = createProcessor();
      expect(() => {
        op.processOrder([{ productId: "FAKE", quantity: 1 }], 0, 0);
      }).toThrow("Product not found");
    });
  });
});
