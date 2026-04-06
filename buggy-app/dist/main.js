"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const orderProcessor_1 = require("./orderProcessor");
const op = new orderProcessor_1.OrderProcessor();
op.addProduct({ id: "LAPTOP", name: "Laptop Pro", price: 999.99, stock: 10 });
op.addProduct({ id: "MOUSE", name: "Wireless Mouse", price: 29.99, stock: 50 });
op.addProduct({ id: "KB", name: "Mechanical Keyboard", price: 149.99, stock: 25 });
const order = op.processOrder([
    { productId: "LAPTOP", quantity: 1 },
    { productId: "MOUSE", quantity: 2 },
    { productId: "KB", quantity: 1 },
], 10, // 10% discount
0.08);
console.log("Order summary:");
for (const item of order.items) {
    console.log(`  ${item.name} x${item.quantity} = $${item.lineTotal.toFixed(2)}`);
}
console.log(`  Subtotal:  $${order.subtotal.toFixed(2)}`);
console.log(`  Discount:  -$${order.discountAmount.toFixed(2)}`);
console.log(`  Tax:        $${order.taxAmount.toFixed(2)}`);
console.log(`  Total:      $${order.total.toFixed(2)}`);
