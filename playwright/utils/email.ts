export function generateEmail(title: string): string {
    const slug = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
    const unix = Math.floor(Date.now() / 1000);
    return `e2e+${slug}-${unix}@example.com`;
}