import { expect, test } from "@tests/fixtures.ts";
import { generateEmail } from "@tests/utils.ts";

test.describe("Setup", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  let email: string;

  test.beforeEach(async ({ page, mailpitAPI }) => {
    email = generateEmail();
    await page.goto("/signup");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("Password123!");
    await page.getByRole("button", { name: "Signup" }).click();

    await expect(page).toHaveURL("/verification");

    const messageId = await mailpitAPI.getLastMessageId(email);
    const code = await mailpitAPI.getVerificationCode(messageId);
    await page.getByLabel("Email verification").fill(code);

    await expect(page).toHaveURL("/setup");
  });

  test("Has default email set", async ({ page }) => {
    await expect(page.getByLabel("Name")).toHaveValue("");
    await expect(page.getByLabel("Email")).toHaveValue(email);
    await expect(
      page.getByRole("button", { name: "Select country" }),
    ).toBeVisible();
  });

  test("Cannot submit with empty country", async ({ page }) => {
    await page.getByLabel("Name").fill("Acme Corporation");
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Country is required")).toBeVisible();
  });

  test("Cannot submit with empty name", async ({ page }) => {
    await page.getByRole("button", { name: "Select country" }).click();
    await page.getByRole("option", { name: "United States" }).click();
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Name is required")).toBeVisible();
    await expect(page.getByText("Country is required")).not.toBeVisible();
  });

  test("Setup account successfully", async ({ page }) => {
    await page.getByLabel("Name").fill("Acme Corporation");
    await page.getByRole("button", { name: "Select country" }).click();
    await page.getByRole("option", { name: "United States" }).click();
    await page.getByRole("button", { name: "Submit" }).click();

    // TODO: fix it to redirect to /onboarding
    await expect(page).toHaveURL("/overview");
  });
});
