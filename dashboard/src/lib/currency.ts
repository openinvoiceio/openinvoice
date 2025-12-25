import { CurrencyEnum } from "@/api/models/currencyEnum";
import Decimal from "decimal.js";

const displayNames = new Intl.DisplayNames(["en"], { type: "currency" });

export const currencies = Object.values(CurrencyEnum).map((code) => ({
  code,
  description: displayNames.of(code) ?? code,
}));

export function isZeroDecimalCurrency(code: string): boolean {
  return (
    new Intl.NumberFormat("en", {
      style: "currency",
      currency: code,
    }).resolvedOptions().maximumFractionDigits === 0
  );
}

export function sanitizeCurrencyAmount(
  value: string | undefined,
  code: string,
): string {
  const decimalValue = new Decimal(value || "0");
  return isZeroDecimalCurrency(code)
    ? decimalValue.toDecimalPlaces(0).toString()
    : decimalValue.toDecimalPlaces(2).toString();
}
