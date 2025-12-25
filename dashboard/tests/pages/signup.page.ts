import type { Page } from "@playwright/test";

export class SignupPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/signup");
  }

  async signup(email: string, password: string) {
    await this.page.getByLabel("Email").fill(email);
    await this.page.getByLabel("Password").fill(password);
    await this.page.getByRole("button", { name: "Signup" }).click();
  }
}
