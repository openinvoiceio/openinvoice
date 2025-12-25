import type { PriceTier } from "@/api/models";
import { useFieldArray } from "react-hook-form";

function normalizeTiersFrom(
  tiers: PriceTier[],
  startIndex: number,
): PriceTier[] {
  const next = tiers.map((t) => ({ ...t }));
  const length = next.length;
  if (length === 0 || startIndex >= length) return next;

  let from: number;

  if (startIndex === 0) {
    // keep first tier's from_value, start reflow from index 1
    from = Number(next[0].from_value);
    startIndex = 1;
  } else {
    const prev = next[startIndex - 1];
    const prevTo =
      prev.to_value != null ? Number(prev.to_value) : Number(prev.from_value);
    from = prevTo + 1;
  }

  for (let i = startIndex; i < length; i++) {
    const current = next[i];
    const isLast = i === length - 1;

    const currentFrom = Number(current.from_value);
    const currentTo =
      current.to_value != null ? Number(current.to_value) : null;

    const span = currentTo == null ? null : currentTo - currentFrom;

    const newFrom = from;
    const newTo = isLast ? null : span == null ? newFrom : newFrom + span;

    next[i] = {
      ...current,
      from_value: newFrom,
      to_value: newTo,
    };

    if (newTo != null) {
      from = newTo + 1;
    }
  }

  return next;
}

export function usePriceTiers({ form }: { form: any }) {
  const tiers = useFieldArray({
    control: form.control,
    name: "tiers",
  });

  function getTiers(): PriceTier[] {
    return form.getValues("tiers") as PriceTier[];
  }

  function setTierValue(index: number, key: keyof PriceTier, value: any) {
    form.setValue(
      `tiers.${index}.${key}` as any,
      value as PriceTier[typeof key],
    );
  }

  function replaceTiers(next: PriceTier[]) {
    (tiers.replace as (value: PriceTier[]) => void)(next);
  }

  function onTierChange(index: number, raw: string | null | undefined) {
    const to_value =
      raw && raw.trim() !== "" ? Math.max(0, Number.parseInt(raw, 10)) : null;

    setTierValue(index, "to_value", to_value);

    if (to_value === null) return;

    const values = getTiers();
    const normalized = normalizeTiersFrom(values, index + 1);

    for (let i = index + 1; i < normalized.length; i++) {
      setTierValue(i, "from_value", normalized[i].from_value);
      setTierValue(i, "to_value", normalized[i].to_value);
    }
  }

  function onTierCreate() {
    const values = getTiers();
    const lastIndex = values.length - 1;
    const last = values[lastIndex];

    const lastFrom = Number(last.from_value);
    const lastTo = last.to_value != null ? Number(last.to_value) : null;

    const newFrom = lastTo != null ? lastTo + 1 : lastFrom + 1;

    setTierValue(lastIndex, "to_value", newFrom - 1);

    tiers.append({
      unit_amount: last.unit_amount,
      from_value: newFrom,
      to_value: null,
    });
  }

  function onTierRemove(index: number) {
    const values = getTiers();
    const length = values.length;

    if (length <= 2) return;

    const without = values.filter((_, i) => i !== index);
    const startIndex = Math.min(index, without.length - 1);
    const normalized = normalizeTiersFrom(without, startIndex);

    replaceTiers(normalized);
  }

  return {
    tiers,
    onTierChange,
    onTierCreate,
    onTierRemove,
  };
}
