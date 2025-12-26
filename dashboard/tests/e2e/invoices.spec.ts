import { expect, test } from "@tests/fixtures.ts";
import { UUID4 } from "@tests/utils.ts";

test.describe("Create invoice", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/invoices");
    await page
      .locator("header")
      .getByRole("button", { name: "Add invoice" })
      .click();
  });

  test("Cannot create invoice without customer", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: "Create invoice" }),
    ).toBeDisabled();
  });

  test("Create invoice with customer only", async ({ page, context }) => {
    const customerName = "Test Customer";
    await context.request.post("/api/v1/customers", {
      data: { name: customerName },
    });

    await page.getByRole("button", { name: "Select customer" }).click();
    await page.getByRole("option", { name: customerName }).click();
    await page.getByRole("button", { name: "Create invoice" }).click();

    await expect(page.getByText("Invoice created")).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`/invoices/${UUID4.source}/edit`));
  });
});
