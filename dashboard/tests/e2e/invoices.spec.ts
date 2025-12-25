import { expect, test } from "@tests/fixtures.ts";
import { UUID4 } from "@tests/utils/regex.ts";

test.describe("Create invoice", () => {
  test.beforeEach(async ({ account }) => {});

  test("Cannot create invoice without customer", async ({
    page,
    invoicesPage,
  }) => {
    await invoicesPage.goto();
    await invoicesPage.addInvoiceButton.click();
    await expect(
      page.getByRole("button", { name: "Create invoice" }),
    ).toBeDisabled();
  });

  test("Create invoice with customer only", async ({
    page,
    customersPage,
    invoicesPage,
  }) => {
    const customerName = "Test Customer";
    await customersPage.goto();
    await customersPage.addCustomer(customerName);

    await invoicesPage.goto();
    await invoicesPage.addInvoiceButton.click();
    await page.getByRole("button", { name: "Select customer" }).click();
    await page.getByRole("option", { name: customerName }).click();
    await page.getByRole("button", { name: "Create invoice" }).click();

    await expect(page.getByText("Invoice created")).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`/invoices/${UUID4.source}/edit`));
  });
});
