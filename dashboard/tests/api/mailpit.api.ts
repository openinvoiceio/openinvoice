import { expect, type APIRequestContext } from "@playwright/test";

const CODE_REGEX = /\b[A-Z0-9]{6}\b/;

export class MailpitAPI {
  constructor(private request: APIRequestContext) {}

  async getLastMessageId(email: string) {
    const response = await this.request.get("/api/v1/search", {
      params: { query: email },
    });
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    return data?.messages?.[0]?.ID;
  }

  async getVerificationCode(messageId: string): Promise<string> {
    const response = await this.request.get(`/api/v1/message/${messageId}`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    const body: string = data.Text || data.HTML || "";

    const match = body.match(CODE_REGEX);
    if (match?.[0]) return match[0];

    throw new Error(`Verification code not found in message ID: ${messageId}`);
  }
}
