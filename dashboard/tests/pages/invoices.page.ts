import type { Locator, Page } from "@playwright/test";

export class InvoicesPage {
  readonly page: Page;
  readonly addInvoiceButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.addInvoiceButton = this.page.locator("header").getByRole("button", {
      name: "Add invoice",
    });
  }

  async goto() {
    await this.page.goto("/invoices");
  }
}
