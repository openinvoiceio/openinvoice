import { CountryEnum } from "@/api/models/countryEnum";

const displayNames = new Intl.DisplayNames(["en"], { type: "region" });

export const countries = Object.values(CountryEnum).map((code) => ({
  code,
  name: displayNames.of(code) ?? code,
}));
