import {
  PriceModelEnum,
  type DefaultPrice,
  type Price,
  type Product,
} from "@/api/models";
import { formatAmount } from "@/lib/formatters.ts";

export function formatPrices(product?: Product) {
  if (!product) return "-";
  const { prices_count, default_price } = product;
  let content: string;
  if (!prices_count) {
    content = "-";
  } else if (prices_count === 1) {
    content = default_price ? formatPrice(default_price) : "1 price";
  } else {
    content = `${prices_count} prices`;
  }
  return content;
}

export function formatPrice(price: Price | DefaultPrice) {
  const { model, tiers, amount, currency } = price;
  if (model === PriceModelEnum.flat) {
    return formatAmount(amount || "0", currency);
  } else if (
    model === PriceModelEnum.volume ||
    model === PriceModelEnum.graduated
  ) {
    const firstTier = tiers?.[0];
    return `Starts at ${formatAmount(firstTier?.unit_amount || 0, currency)}`;
  }
  return "-";
}
