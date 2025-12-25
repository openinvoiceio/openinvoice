import { clsx } from "clsx";
import type { ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: Array<ClassValue>) {
  return twMerge(clsx(inputs));
}

export function recordToList<K extends string, V>(
  record: Record<K, V> | undefined | null,
): { key: K; value: V }[] {
  if (!record) return [];
  return Object.entries(record).map(([key, value]) => ({
    key: key as K,
    value: value as V,
  }));
}

export function listToRecord<K extends string, V>(
  list: { key: K; value: V }[],
): Record<K, V> {
  return list.reduce<Record<K, V>>(
    (acc, { key, value }) => {
      acc[key] = value;
      return acc;
    },
    {} as Record<K, V>,
  );
}
