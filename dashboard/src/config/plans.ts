import { ENTERPRISE_PRICE_ID, STANDARD_PRICE_ID } from "@/lib/stripe";

export const plans = [
  {
    title: "Free",
    id: "free",
    priceId: undefined,
    description: "Perfect to get started",
    price: 0,
    limits: {
      invoices: 20,
      customers: 20,
      products: 20,
      members: 1,
      "invoice emailing": false,
      "numbering systems": false,
      "24/7 support": false,
    },
  },
  {
    title: "Standard",
    id: "standard",
    priceId: STANDARD_PRICE_ID,
    description: "Perfect for individuals and small teams",
    price: 10,
    limits: {
      invoices: 100,
      customers: 100,
      products: 100,
      members: 5,
      "invoice emailing": true,
      "numbering systems": true,
      "24/7 support": false,
    },
  },
  {
    title: "Enterprise",
    id: "enterprise",
    priceId: ENTERPRISE_PRICE_ID,
    description: "Perfect for enterprises and large teams",
    price: 100,
    limits: {
      invoices: Infinity,
      customers: Infinity,
      products: Infinity,
      members: Infinity,
      "invoice emailing": true,
      "numbering systems": true,
      "24/7 support": true,
    },
  },
];
