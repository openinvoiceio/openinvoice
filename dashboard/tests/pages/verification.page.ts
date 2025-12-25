import type { Page } from "@playwright/test";

export class VerificationPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/verification");
  }

  async verify(code: string) {
    await this.page.getByLabel("Email verification").fill(code);
  }
}
