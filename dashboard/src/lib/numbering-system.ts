export const templatePattern = /\{(?:yyyy|yy|q|mm|m|n+)}/g;

export function renderTemplate(
  template: string,
  count: number = 1233,
  timestamp = new Date(),
): string {
  const yearFull = timestamp.getFullYear();
  const yearShort = String(yearFull % 100).padStart(2, "0");
  const quarter = Math.floor(timestamp.getMonth() / 3) + 1;
  const monthFull = String(timestamp.getMonth() + 1).padStart(2, "0");
  const monthShort = String(timestamp.getMonth() + 1);
  return template.replace(templatePattern, (token) => {
    switch (token) {
      case "{yyyy}":
        return String(yearFull);
      case "{yy}":
        return yearShort;
      case "{q}":
        return String(quarter);
      case "{mm}":
        return monthFull;
      case "{m}":
        return monthShort;
      default: {
        // {n...}
        if (/^\{n+\}$/.test(token)) {
          const width = token.length - 2;
          return String(count + 1).padStart(width, "0");
        }
        return token;
      }
    }
  });
}
