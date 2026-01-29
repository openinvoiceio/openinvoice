import { format, formatDistanceToNow, fromUnixTime, parseISO } from "date-fns";
import { enUS } from "date-fns/locale";
import Decimal from "decimal.js";

const regionDisplayNames = new Intl.DisplayNames(["en"], { type: "region" });

export function formatDate(value?: string | number | Date): string {
  if (!value) return "";
  const date: Date = value instanceof Date ? value : new Date(value);
  return format(date, "LLLL dd, y", { locale: enUS });
}

export function formatFilterDate(value?: string | number | Date): string {
  if (!value) return "";
  const date: Date = value instanceof Date ? value : new Date(value);
  return format(date, "LLL dd, y", { locale: enUS });
}

export function formatISODate(value?: string | number | Date): string {
  if (!value) return "";
  const date: Date = value instanceof Date ? value : new Date(value);
  return format(date, "yyyy-MM-dd");
}

export function formatDatetime(value?: number | Date | string): string {
  if (!value) return "";
  const date: Date =
    value instanceof Date
      ? value
      : typeof value === "number"
        ? fromUnixTime(value)
        : parseISO(value);

  return format(date, "LLLL dd, y HH:mm:ss", { locale: enUS });
}

export function formatRelativeDatetime(value: string | Date) {
  const date = typeof value === "string" ? parseISO(value) : value;

  return formatDistanceToNow(date, {
    addSuffix: true,
  });
}

export function formatAmount(value: number | string, currency: string) {
  const decimalPrice = new Decimal(value);

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency,
    signDisplay: "never",
    maximumFractionDigits: 2,
  }).format(decimalPrice.toNumber());
}

export function formatPercentage(value: string): string {
  return `${new Decimal(value).toString()} %`;
}

export function formatCountry(value: string) {
  return regionDisplayNames.of(value) ?? "";
}

export function formatTaxIdType(value: string) {
  return value.replace(/_/g, " ").toUpperCase();
}

export function formatEmailList(emails: string[], maxVisible = 2): string {
  if (emails.length <= maxVisible) {
    return emails.join(", ");
  }

  const visibleEmails = emails.slice(0, maxVisible).join(", ");
  const remainingCount = emails.length - maxVisible;
  return `${visibleEmails}, + ${remainingCount} more`;
}

export function formatEnum(value: string) {
  const formatted = value.replace(/_/g, " ");
  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

export function formatNetPaymentTerm(value: number): string {
  if (value === -1) return "Custom";
  if (value === 0) return "Today";
  if (value === 1) return "Tomorrow";
  return `${value} days`;
}

export function formatDueDate(value: number): string {
  if (value === -1) return "Due custom date";
  if (value === 0) return "Due today";
  if (value === 1) return "Due tomorrow";
  return `Due in ${value} days`;
}
