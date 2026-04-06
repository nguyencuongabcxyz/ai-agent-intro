export interface Product {
  id: string;
  name: string;
  price: number;       // unit price in dollars
  stock: number;        // available inventory
}

export interface OrderItem {
  productId: string;
  quantity: number;
}

export interface OrderResult {
  items: {
    productId: string;
    name: string;
    unitPrice: number;
    quantity: number;
    lineTotal: number;
  }[];
  subtotal: number;
  discountAmount: number;
  taxAmount: number;
  total: number;
}

export interface InventoryUpdate {
  productId: string;
  oldStock: number;
  newStock: number;
}
