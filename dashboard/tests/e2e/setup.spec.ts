import { expect, test } from "@tests/fixtures.ts";

test.describe("Setup", () => {
  test("Has default email set", async ({ page, user }) => {
    await expect(page).toHaveURL("/setup");
    await expect(page.getByLabel("Name")).toHaveValue("");
    await expect(page.getByLabel("Email")).toHaveValue(user.email);
    await expect(
      page.getByRole("button", { name: "Select country" }),
    ).toBeVisible();
  });

  test("Cannot submit with empty country", async ({ page, user }) => {
    await page.getByLabel("Name").fill("Acme Corporation");
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Country is required")).toBeVisible();
  });

  test("Cannot submit with empty name", async ({ page, user }) => {
    await page.getByRole("button", { name: "Select country" }).click();
    await page.getByRole("option", { name: "United States" }).click();
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Name is required")).toBeVisible();
    await expect(page.getByText("Country is required")).not.toBeVisible();
  });

  test("Setup account successfully", async ({ page, user }) => {
    await page.getByLabel("Name").fill("Acme Corporation");
    await page.getByRole("button", { name: "Select country" }).click();
    await page.getByRole("option", { name: "United States" }).click();
    await page.getByRole("button", { name: "Submit" }).click();

    // TODO: fix it to redirect to /onboarding
    await expect(page).toHaveURL("/overview");
  });
});
