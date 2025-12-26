import type { BrowserContext } from "@playwright/test";

export const UUID4 =
  /[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i;

export function generateEmail(id?: string): string {
  id = id ? id : Math.random().toString(36).substring(2, 10);
  const unix = Math.floor(Date.now() / 1000);
  return `e2e+${id}-${unix}@example.com`;
}

export async function setCsrfHeader(context: BrowserContext) {
  const cookies = await context.cookies();
  const token = cookies.find((c) => c.name === "csrftoken")?.value;
  if (!!token) await context.setExtraHTTPHeaders({ "x-csrftoken": token });
}
