import fs from "fs";
import path from "path";
import { test as base, expect, request } from "@playwright/test";
import { MailpitAPI } from "@tests/api/mailpit.api.ts";
import { generateEmail, setCsrfHeader } from "@tests/utils.ts";

export type TestOptions = {};
export type WorkerOptions = {
  workerStorageState: string;
  mailpitURL: string;
  mailpitAPI: MailpitAPI;
};

export const test = base.extend<TestOptions, WorkerOptions>({
  mailpitURL: ["", { option: true, scope: "worker" }],
  mailpitAPI: [
    async ({ mailpitURL }, use) => {
      const context = await request.newContext({
        baseURL: mailpitURL,
      });
      await use(new MailpitAPI(context));
    },
    { scope: "worker" },
  ],
  storageState: ({ workerStorageState }, use) => use(workerStorageState),
  workerStorageState: [
    async ({ browser, mailpitAPI }, use) => {
      // Use parallelIndex as a unique identifier for each worker.
      const id = test.info().parallelIndex;
      const fileName = path.resolve(
        test.info().project.outputDir,
        `.auth/${id}.json`,
      );
      const baseURL = test.info().project.use.baseURL;

      if (fs.existsSync(fileName)) {
        // Reuse existing authentication state if any.
        await use(fileName);
        return;
      }

      // Important: make sure we authenticate in a clean environment by unsetting storage state.
      const page = await browser.newPage({
        storageState: undefined,
        baseURL,
      });
      const context = page.context();

      // Acquire a unique account, for example create a new one.
      // Alternatively, you can have a list of precreated accounts for testing.
      // Make sure that accounts are unique, so that multiple team members
      // can run tests at the same time without interference.
      const email = generateEmail();
      const password = "Password123!";
      // Get csrf cookie
      await page.request.head("/api/browser/v1/auth/signup", {
        data: { email, password },
      });
      await setCsrfHeader(context);

      // Sign up
      let response = await page.request.post("/api/browser/v1/auth/signup", {
        data: { email, password },
      });
      if (response.status() !== 401) throw new Error("Failed to sign up");

      const messageId = await mailpitAPI.getLastMessageId(email);
      const code = await mailpitAPI.getVerificationCode(messageId);

      // Verify
      response = await page.request.post("/api/browser/v1/auth/email/verify", {
        data: { key: code },
      });
      if (response.status() !== 200)
        throw new Error("Failed to verify account");

      await setCsrfHeader(context);

      await page.request.post("/api/v1/accounts", {
        data: { name: `Account ${id}`, country: "US", email },
      });

      // End of authentication steps.

      await context.storageState({ path: fileName });
      await page.close();
      await use(fileName);
    },
    { scope: "worker" },
  ],
  context: async ({ context }, use) => {
    await setCsrfHeader(context);
    await use(context);
  },
});

export { expect };
