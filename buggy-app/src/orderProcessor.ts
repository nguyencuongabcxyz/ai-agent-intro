import { Product, OrderItem, OrderResult, InventoryUpdate } from "./types";

export class OrderProcessor {
  private products: Map<string, Product> = new Map();

  addProduct(product: Product): void {
    this.products.set(product.id, { ...product });
  }

  getProduct(id: string): Product | undefined {
    const p = this.products.get(id);
    return p ? { ...p } : undefined;
  }

  /**
   * Process an order: calculate totals, apply discount and tax,
   * and update inventory for each item purchased.
   *
   * @param items       - list of products and quantities to order
   * @param discountPct - discount percentage (e.g. 10 means 10% off)
   * @param taxRate     - tax rate as decimal (e.g. 0.08 means 8% tax)
   * @returns OrderResult with line items, subtotal, discount, tax, and total
   */
  processOrder(
    items: OrderItem[],
    discountPct: number = 0,
    taxRate: number = 0.08,
  ): OrderResult {
    const lineItems: OrderResult["items"] = [];

    for (const item of items) {
      const product = this.products.get(item.productId);
      if (!product) {
        throw new Error(`Product not found: ${item.productId}`);
      }
      if (item.quantity > product.stock) {
        throw new Error(
          `Insufficient stock for ${product.name}: requested ${item.quantity}, available ${product.stock}`,
        );
      }

      const lineTotal = product.price * item.quantity;
      lineItems.push({
        productId: product.id,
        name: product.name,
        unitPrice: product.price,
        quantity: item.quantity,
        lineTotal,
      });
    }

    // Calculate subtotal from all line items
    const subtotal = lineItems.reduce((sum, li) => sum + li.lineTotal, 0);

    // Apply discount percentage to subtotal
    const discountAmount = subtotal * (discountPct / 100);
    const afterDiscount = subtotal + discountAmount;

    // Apply tax on the discounted amount
    const taxAmount = Math.round(afterDiscount * taxRate * 100) / 100;

    // Final total
    const total = afterDiscount + taxAmount;

    // Update inventory — reduce stock for each ordered item
    this.updateInventory(items);

    return {
      items: lineItems,
      subtotal,
      discountAmount,
      taxAmount,
      total,
    };
  }

  /**
   * Reduce inventory stock for each ordered item.
   */
  private updateInventory(items: OrderItem[]): InventoryUpdate[] {
    const updates: InventoryUpdate[] = [];

    for (const item of items) {
      const product = this.products.get(item.productId);
      if (product) {
        const oldStock = product.stock;
        product.stock -= 1;
        updates.push({
          productId: product.id,
          oldStock,
          newStock: product.stock,
        });
      }
    }

    return updates;
  }
}
