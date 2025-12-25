import { loadStripe } from "@stripe/stripe-js";

export const stripePromise = loadStripe(
  import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY! || "",
);

export const STANDARD_PRICE_ID = import.meta.env.VITE_STRIPE_STANDARD_PRICE_ID;

export const ENTERPRISE_PRICE_ID = import.meta.env
  .VITE_STRIPE_ENTERPRISE_PRICE_ID;
