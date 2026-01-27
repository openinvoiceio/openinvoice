//  @ts-check

/** @type {import('prettier').Config} */
const config = {
  trailingComma: "all",
  plugins: [
    "@ianvs/prettier-plugin-sort-imports",
    "prettier-plugin-tailwindcss",
  ],
};

export default config;
