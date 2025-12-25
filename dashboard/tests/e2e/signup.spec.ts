import { expect, test } from "@tests/fixtures.ts";
import { generateEmail } from "@tests/utils/email.ts";

const VALID_PASSWORD = "Password123!";

test.describe("Signup", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/signup");
  });

  test("Cannot signup with invalid email", async ({ page }) => {
    await page.getByLabel("Email").fill("test@example.c");
    await page.getByLabel("Password").fill(VALID_PASSWORD);
    await page.getByRole("button", { name: "Signup" }).click();

    await expect(page.getByText("Invalid email address")).toBeVisible();
  });

  test("Cannot signup with weak password", async ({ page }, { title }) => {
    const email = generateEmail(title);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("weak");
    await page.getByRole("button", { name: "Signup" }).click();

    await expect(
      page.getByText("Password must be at least 8 characters"),
    ).toBeVisible();
  });

  test("Cannot signup with numeric password", async ({ page }, { title }) => {
    const email = generateEmail(title);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("12345678");
    await page.getByRole("button", { name: "Signup" }).click();

    await expect(
      page.getByText("Password cannot be entirely numeric."),
    ).toBeVisible();
  });

  test("Cannot signup when signup is closed", async ({ page }, { title }) => {
    const email = generateEmail(title);
    await page.route("**/api/browser/v1/auth/signup", (route) => {
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({
          type: "client_error",
          errors: [{ detail: "Permission denied" }],
        }),
      });
    });

    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(VALID_PASSWORD);
    await page.getByRole("button", { name: "Signup" }).click();

    await expect(page.getByText("Signup failed")).toBeVisible();
  });

  test("Cannot verify email with invalid code", async ({ page }, { title }) => {
    const email = generateEmail(title);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(VALID_PASSWORD);
    await page.getByRole("button", { name: "Signup" }).click();

    await expect(page).toHaveURL("/verification");

    await page.getByLabel("Email verification").fill("000000");

    await expect(page.getByText("Incorrect code.")).toBeVisible();
  });

  test("Cannot verify email with expired code", async ({ page }, { title }) => {
    const email = generateEmail(title);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(VALID_PASSWORD);
    await page.getByRole("button", { name: "Signup" }).click();

    await expect(page).toHaveURL("/verification");

    for (let i = 0; i < 3; i++) {
      await page.getByLabel("Email verification").clear();
      await page.getByLabel("Email verification").fill("000000");
      await expect(page.getByText("Incorrect code.")).toBeVisible();
    }

    await page.getByLabel("Email verification").clear();
    await page.getByLabel("Email verification").fill("000000");

    await expect(page).toHaveURL("/login");
    await expect(
      page.getByText("Verification code expired. Please login again."),
    ).toBeVisible();
  });

  test("Can signup with verification", async ({ page, mailpitAPI }, {
    title,
  }) => {
    const email = generateEmail(title);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(VALID_PASSWORD);
    await page.getByRole("button", { name: "Signup" }).click();

    await expect(page).toHaveURL("/verification");

    const messageId = await mailpitAPI.getLastMessageId(email);
    const code = await mailpitAPI.getVerificationCode(messageId);
    await page.getByLabel("Email verification").fill(code);

    await expect(page).toHaveURL("/setup");
  });
});
