import { expect, test } from "@tests/fixtures.ts";
import { UUID4 } from "@tests/utils.ts";

test.describe("Create customer", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/customers");
    await page
      .locator("header")
      .getByRole("button", { name: "Add customer" })
      .click();
  });

  test("Cannot create customer with empty name", async ({ page }) => {
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Name is required")).toBeVisible();
  });

  test("Create customer with only name", async ({ page }) => {
    await page.getByLabel("Name", { exact: true }).fill("John Doe");
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Customer created")).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`/customers/${UUID4.source}/edit`));
  });

  test("Create customer with all filled fields", async ({ page }) => {
    await page.getByLabel("Name", { exact: true }).fill("John Doe");
    await page.getByLabel("Legal name").fill("Johnathan Doe LLC");
    await page.getByLabel("Legal number").fill("123456789");
    await page.getByLabel("Email").fill("test-customer@example.com");
    await page.getByRole("button", { name: "Select currency" }).click();
    await page.getByRole("option", { name: "USD" }).click();
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Customer created")).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`/customers/${UUID4.source}/edit`));
  });
});
