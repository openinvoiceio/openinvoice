import type { Locator, Page } from "@playwright/test";

export class CustomersPage {
  readonly page: Page;
  readonly addCustomerButton: Locator;
  readonly createCustomerDialog: Locator;

  constructor(page: Page) {
    this.page = page;
    this.addCustomerButton = this.page.locator("header").getByRole("button", {
      name: "Add customer",
    });
    this.createCustomerDialog = this.page.getByRole("dialog", {
      name: "Create Customer",
    });
  }

  async goto() {
    await this.page.goto("/customers");
  }

  async addCustomer(name: string) {
    await this.addCustomerButton.click();
    await this.createCustomerDialog
      .getByLabel("Name", { exact: true })
      .fill(name);
    await this.createCustomerDialog
      .getByRole("button", { name: "Submit" })
      .click();
  }
}
