import {APIRequestContext, expect} from "@playwright/test";

const MAILPIT_URL = process.env.MAILPIT_URL ?? "http://localhost:8025";
const CODE_REGEX = /\b[A-Z0-9]{6}\b/;


export async function getVerificationCode(
    request: APIRequestContext,
    toEmail: string,
    {
        timeoutMs = 10_000,
        pollMs = 300,
    } = {}
): Promise<string> {
    const started = Date.now();

    while (Date.now() - started < timeoutMs) {
        // 1) search messages
        const searchRes = await request.get(`${MAILPIT_URL}/api/v1/search`, {
            params: {query: toEmail},
        });
        expect(searchRes.ok()).toBeTruthy();

        const searchData = await searchRes.json();
        const msg = searchData?.messages?.[0];
        if (!msg?.ID) {
            await new Promise((r) => setTimeout(r, pollMs));
            continue;
        }

        // fetch message
        const msgRes = await request.get(`${MAILPIT_URL}/api/v1/message/${msg.ID}`);
        expect(msgRes.ok()).toBeTruthy();

        const msgData = await msgRes.json();
        const body: string = msgData.Text || msgData.HTML || "";

        // extract code
        const match = body.match(CODE_REGEX);
        if (match?.[0]) return match[0];

        // message exists but code not yet in body / unexpected format
        await new Promise((r) => setTimeout(r, pollMs));
    }

    throw new Error(`Timeout: could not get verification code for ${toEmail}`);
}