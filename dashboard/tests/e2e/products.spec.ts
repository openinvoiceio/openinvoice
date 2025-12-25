import { expect, test } from "@tests/fixtures.ts";

test.describe("Create product", () => {
  test.beforeEach(async ({ page, account }) => {
    await page.getByRole("link", { name: "Product catalogue" }).click();
    await expect(page).toHaveURL("/products");
    await page
      .locator("header")
      .getByRole("button", { name: "Add product" })
      .click();
  });

  test("Cannot create product with empty name", async ({ page }) => {
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Name is required")).toBeVisible();
  });

  test("Create product with only name", async ({ page }) => {
    await expect(page.getByRole("button", { name: "USD" })).toBeVisible();

    await page.getByLabel("Name", { exact: true }).fill("Sample Product");
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Product created")).toBeVisible();
    await expect(page).toHaveURL("/products");
  });

  test("Create customer with all filled fields", async ({ page }) => {
    await page.getByLabel("Name").fill("Sample Product");
    await page
      .getByLabel("Description")
      .fill("This is a sample product description.");
    // TODO: add test for image upload
    await page.getByLabel("Amount").fill("19.99");
    await page.getByRole("button", { name: "USD" }).click();
    await page.getByRole("option", { name: "EUR" }).click();
    await page.getByLabel("Code").fill("SP-001");
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Product created")).toBeVisible();
    await expect(page).toHaveURL("/products");
  });
});
