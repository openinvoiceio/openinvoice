import type { Page } from "@playwright/test";

export class SetupPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/setup");
  }

  async fillEmail(email: string) {
    await this.page.getByLabel("Email").fill(email);
  }

  async setup(name: string, country: string) {
    await this.page.getByLabel("Name").fill(name);
    await this.page.getByRole("button", { name: "Select country" }).click();
    await this.page.getByRole("option", { name: country }).click();
    await this.page.getByRole("button", { name: "Submit" }).click();
  }
}
