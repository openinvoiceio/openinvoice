import {test as base, expect} from "@playwright/test";
import {generateEmail} from "./email";
import {getVerificationCode} from "./mailpit";

const VALID_PASSWORD = "Password123!";

type AuthFixtures = {
    signup: (opts?: { password?: string; goto?: boolean }) => Promise<{ email: string; }>;
    setupAccount: (opts?: { goto?: boolean }) => Promise<{ email: string }>;
};

export const test = base.extend<AuthFixtures>({
    signup: async ({page, request}, use, testInfo) => {
        await use(async (opts) => {
            const email = generateEmail(testInfo.title);
            const password = opts?.password ?? VALID_PASSWORD;

            if (opts?.goto ?? true) await page.goto("/signup");

            await page.getByLabel("Email").fill(email);
            await page.getByLabel("Password").fill(password);
            await page.getByRole("button", {name: "Signup"}).click();

            await expect(page).toHaveURL("/verification");

            const code = await getVerificationCode(request, email);
            await page.getByLabel("Email verification").fill(code);

            return {email};
        });
    },
    setupAccount: async ({page, signup}, use, testInfo) => {
        await use(async (opts) => {
            const {email} = await signup({goto: opts?.goto ?? true});

            await page.getByLabel("Name").fill("Acme Corporation");
            await page.getByRole("button", {name: "Select country"}).click();
            await page.getByRole("option", {name: "United States"}).click();
            await page.getByRole("button", {name: "Submit"}).click();

            return {email};
        });
    },
});

export {expect};
