import {expect, test} from "../utils/base";


test.describe("Setup", () => {

    test('Has default email set', async ({page, signup}) => {
        const {email} = await signup();

        await expect(page).toHaveURL("/setup")
        await expect(page.getByLabel("Name")).toHaveValue("")
        await expect(page.getByLabel("Email")).toHaveValue(email)
        await expect(page.getByRole("button", {name: "Select country"})).toBeVisible()
    })

    test("Cannot submit with empty country", async ({page, signup}) => {
        await signup();

        await page.getByLabel("Name").fill("Acme Corporation");
        await page.getByRole("button", {name: "Submit"}).click();

        await expect(page.getByText("Country is required")).toBeVisible();
    })

    test("Cannot submit with empty name", async ({page, signup}) => {
        await signup();

        await page.getByRole("button", {name: "Select country"}).click();
        await page.getByRole("option", {name: "United States"}).click();
        await page.getByRole("button", {name: "Submit"}).click();

        await expect(page.getByText("Name is required")).toBeVisible();
        await expect(page.getByText("Country is required")).not.toBeVisible();
    })


    test("Setup account successfully", async ({page, signup}) => {
        await signup();

        await page.getByLabel("Name").fill("Acme Corporation");
        await page.getByRole("button", {name: "Select country"}).click();
        await page.getByRole("option", {name: "United States"}).click();
        await page.getByRole("button", {name: "Submit"}).click();

        await expect(page).toHaveURL("/onboarding")
    })
});
