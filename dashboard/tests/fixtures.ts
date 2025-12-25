import { test as base, expect, request } from "@playwright/test";
import { MailpitAPI } from "@tests/api/mailpit.api.ts";
import { CustomersPage } from "@tests/pages/customers.page.ts";
import { InvoicesPage } from "@tests/pages/invoices.page.ts";
import { SetupPage } from "@tests/pages/setup.page.ts";
import { SignupPage } from "@tests/pages/signup.page.ts";
import { VerificationPage } from "@tests/pages/verification.page.ts";
import { generateEmail } from "@tests/utils/email.ts";

type Fixtures = {
  email: string;
  mailpitAPI: MailpitAPI;
  signupPage: SignupPage;
  verificationPage: VerificationPage;
  setupPage: SetupPage;
  customersPage: CustomersPage;
  invoicesPage: InvoicesPage;
  user: { email: string; password: string };
  account: { name: string; email: string; country: string };
  signup: (opts?: {
    password?: string;
    goto?: boolean;
  }) => Promise<{ email: string }>;
  setupAccount: (opts?: { goto?: boolean }) => Promise<{ email: string }>;
};

export const test = base.extend<Fixtures>({
  email: async ({}, use, testInfo) => {
    const email = generateEmail(testInfo.title);
    await use(email);
  },
  mailpitAPI: async ({}, use) => {
    const context = await request.newContext({
      baseURL: process.env.MAILPIT_URL ?? "http://localhost:8025",
    });
    await use(new MailpitAPI(context));
  },
  signupPage: async ({ page }, use) => {
    await use(new SignupPage(page));
  },
  verificationPage: async ({ page }, use) => {
    await use(new VerificationPage(page));
  },
  setupPage: async ({ page }, use) => {
    await use(new SetupPage(page));
  },
  customersPage: async ({ page }, use) => {
    await use(new CustomersPage(page));
  },
  invoicesPage: async ({ page }, use) => {
    await use(new InvoicesPage(page));
  },
  user: async (
    { page, signupPage, verificationPage, mailpitAPI },
    use,
    testInfo,
  ) => {
    const email = generateEmail(testInfo.title);
    const password = "Password123!";
    await signupPage.goto();
    await signupPage.signup(email, password);
    await expect(page).toHaveURL("/verification");
    const messageId = await mailpitAPI.getLastMessageId(email);
    const code = await mailpitAPI.getVerificationCode(messageId);
    await verificationPage.verify(code);
    await expect(page).toHaveURL("/setup");
    await use({ email, password });
  },
  account: async ({ page, setupPage, user }, use) => {
    await page.screenshot();
    const name = "Acme Corporation";
    const country = "United States";
    await setupPage.goto();
    await setupPage.setup(name, country);
    await use({ name, email: user.email, country });
  },
});

export { expect };
