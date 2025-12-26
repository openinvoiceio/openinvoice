import { faker } from "@faker-js/faker/locale/en";
import { expect, test } from "@tests/fixtures.ts";

test.describe("Edit invoice", () => {
  test.beforeEach(async ({ page, context }) => {
    const customerId = await context.request
      .post("/api/v1/customers", {
        data: { name: faker.company.name() },
      })
      .then((res) => res.json().then((data) => data.id));
    const invoiceId = await context.request
      .post("/api/v1/invoices", {
        data: { customer_id: customerId },
      })
      .then((res) => res.json().then((data) => data.id));
    await page.goto(`/invoices/${invoiceId}/edit`);
  });

  test("Add invoice line with one-time price", async ({ page }) => {
    await page.getByRole("button", { name: "Add line" }).click();
    await page.getByRole("button", { name: "Add one-time price" }).click();
    await page
      .getByRole("textbox", { name: "Description" })
      .fill("Standard plan");
    await page.getByRole("textbox", { name: "Price" }).fill("23.00");
    await page.getByRole("textbox", { name: "Quantity" }).fill("4");

    await expect(
      page.getByRole("button", { name: "Standard plan × 4" }),
    ).toBeVisible();
    await expect(page.getByText("One-time")).toBeVisible();
  });

  test("Add invoice line with recurring price", async ({ page, context }) => {
    const productName = faker.commerce.productName();
    await context.request.post("/api/v1/products", {
      data: {
        name: productName,
        default_price: {
          amount: "18.00",
          currency: "USD",
          // TODO: make such fields optional in the backend
          metadata: {},
          code: null,
        },
      },
    });

    await page.getByRole("button", { name: "Add line" }).click();
    await page.getByRole("option", { name: "$18.00" }).click();

    await expect(page.getByLabel("Description")).toHaveValue(productName);
    await expect(
      page
        .getByTestId("invoice-lines-card")
        .getByRole("button", { name: "$18.00" }),
    ).toBeVisible();
    await expect(page.getByLabel("Quantity")).toHaveValue("1");
    await expect(
      page.getByRole("button", { name: `${productName} × 1` }),
    ).toBeVisible();
  });

  test("Add invoice line with fixed discount", async ({ page, context }) => {
    const couponName = `${faker.word.adjective().toUpperCase()}15`;
    await context.request.post("/api/v1/coupons", {
      data: {
        name: couponName,
        amount: 15.0,
      },
    });

    await page.getByRole("button", { name: "Add line" }).click();
    await page.getByRole("button", { name: "Add one-time price" }).click();
    await page
      .getByRole("textbox", { name: "Description" })
      .fill("Standard plan");
    await page.getByRole("textbox", { name: "Price" }).fill("50.00");
    await page.getByRole("textbox", { name: "Quantity" }).fill("2");
    await expect(
      page.getByRole("button", { name: "Standard plan × 2" }),
    ).toBeVisible();

    await page
      .getByTestId("invoice-lines-card")
      .getByRole("button", { name: "Add discount" })
      .click();
    await page.getByRole("option", { name: couponName }).click();

    await expect(
      page.getByLabel("Invoice line header").getByText("$15.00 off"),
    ).toBeVisible();
    await expect(page.getByText(`${couponName}$15.00 off`)).toBeVisible();
    await expect(page.getByText("-$15.00")).toBeVisible();
  });

  test("Add invoice line with percentage discount", async ({
    page,
    context,
  }) => {
    const couponName = `${faker.word.adjective().toUpperCase()}20%`;
    await context.request.post("/api/v1/coupons", {
      data: {
        name: couponName,
        percentage: 20,
      },
    });

    await page.getByRole("button", { name: "Add line" }).click();
    await page.getByRole("button", { name: "Add one-time price" }).click();
    await page
      .getByRole("textbox", { name: "Description" })
      .fill("Standard plan");
    await page.getByRole("textbox", { name: "Price" }).fill("100.00");
    await page.getByRole("textbox", { name: "Quantity" }).fill("1");
    await expect(
      page.getByRole("button", { name: "Standard plan × 1" }),
    ).toBeVisible();

    await page
      .getByTestId("invoice-lines-card")
      .getByRole("button", { name: "Add discount" })
      .click();
    await page.getByRole("option", { name: couponName }).click();

    await expect(page.getByText("$20.00 off")).toBeVisible();
    await expect(page.getByText(`${couponName}20 % off`)).toBeVisible();
    await expect(page.getByText("-$20.00")).toBeVisible();
  });

  test("Add invoice line with tax", async ({ page, context }) => {
    const taxRateName = `VAT 10% ${faker.string.alphanumeric({ length: 4 })}`;
    await context.request.post("/api/v1/tax-rates", {
      data: {
        name: taxRateName,
        percentage: 10,
      },
    });

    await page.getByRole("button", { name: "Add line" }).click();
    await page.getByRole("button", { name: "Add one-time price" }).click();
    await page
      .getByRole("textbox", { name: "Description" })
      .fill("Standard plan");
    await page.getByRole("textbox", { name: "Price" }).fill("40.00");
    await page.getByRole("textbox", { name: "Quantity" }).fill("1");
    await expect(
      page.getByRole("button", { name: "Standard plan × 1" }),
    ).toBeVisible();

    await page
      .getByTestId("invoice-lines-card")
      .getByRole("button", { name: "Add tax" })
      .click();
    await page.getByRole("option", { name: taxRateName }).click();

    await expect(page.getByText("10 % tax")).toBeVisible();
    await expect(page.getByText(`${taxRateName}10 %`)).toBeVisible();
    await expect(page.getByText("$4.00")).toBeVisible();
  });

  test("Remove invoice line", async ({ page }) => {
    await page.getByRole("button", { name: "Add line" }).click();
    await page.getByRole("button", { name: "Add one-time price" }).click();
    await page.getByLabel("Description").fill("Standard plan");
    await page.getByLabel("Price").fill("10.00");

    await expect(
      page.getByRole("button", { name: "Standard plan × 1" }),
    ).toBeVisible();

    await page
      .getByTestId("invoice-lines-card")
      .getByRole("button", { name: "Remove line Standard plan" })
      .click();

    await expect(
      page.getByRole("button", { name: "Standard plan × 1" }),
    ).not.toBeVisible();
  });

  test("Remove invoice line discount", async ({ page, context }) => {
    const couponName = `${faker.word.adjective().toUpperCase()}15`;
    await context.request.post("/api/v1/coupons", {
      data: {
        name: couponName,
        amount: 15.0,
      },
    });

    await page.getByRole("button", { name: "Add line" }).click();
    await page.getByRole("button", { name: "Add one-time price" }).click();
    await page.getByLabel("Description").fill("Standard plan");
    await page.getByLabel("Price").fill("50.00");
    await expect(
      page.getByRole("button", { name: "Standard plan × 1" }),
    ).toBeVisible();

    await page
      .getByTestId("invoice-lines-card")
      .getByRole("button", { name: "Add discount" })
      .click();
    await page.getByRole("option", { name: couponName }).click();

    await expect(page.getByText("-$15.00")).toBeVisible();
    await page
      .getByTestId("invoice-lines-card")
      .getByRole("button", { name: `Remove discount ${couponName}` })
      .click();

    await expect(page.getByText("-$15.00")).not.toBeVisible();
  });

  test("Remove invoice line tax", async ({ page, context }) => {
    const taxRateName = `VAT 10% ${faker.string.alphanumeric({ length: 4 })}`;
    await context.request.post("/api/v1/tax-rates", {
      data: {
        name: taxRateName,
        percentage: 10,
      },
    });

    await page.getByRole("button", { name: "Add line" }).click();
    await page.getByRole("button", { name: "Add one-time price" }).click();
    await page.getByLabel("Description").fill("Standard plan");
    await page.getByLabel("Price").fill("40.00");
    await expect(
      page.getByRole("button", { name: "Standard plan × 1" }),
    ).toBeVisible();

    await page
      .getByTestId("invoice-lines-card")
      .getByRole("button", { name: "Add tax" })
      .click();
    await page.getByRole("option", { name: taxRateName }).click();

    await expect(page.getByText("$4.00")).toBeVisible();
    await page
      .getByTestId("invoice-lines-card")
      .getByRole("button", { name: `Remove tax ${taxRateName}` })
      .click();

    await expect(page.getByText("$4.00")).not.toBeVisible();
  });

  test("Add invoice discount", async ({ page, context }) => {
    const couponName = `${faker.word.adjective().toUpperCase()}10`;
    await context.request.post("/api/v1/coupons", {
      data: {
        name: couponName,
        amount: 10.0,
      },
    });

    await page
      .getByTestId("invoice-discounts-card")
      .getByRole("button", { name: "Add discount" })
      .click();
    await page.getByRole("option", { name: couponName }).click();

    await expect(page.getByText(`${couponName}$10.00 off`)).toBeVisible();
    await expect(page.getByText("-$0.00")).toBeVisible();
  });

  test("Remove invoice discount", async ({ page, context }) => {
    const couponName = `${faker.word.adjective().toUpperCase()}10`;
    await context.request.post("/api/v1/coupons", {
      data: {
        name: couponName,
        amount: 10.0,
      },
    });

    await page
      .getByTestId("invoice-discounts-card")
      .getByRole("button", { name: "Add discount" })
      .click();
    await page.getByRole("option", { name: couponName }).click();

    await expect(page.getByText("-$0.00")).toBeVisible();
    await page
      .getByTestId("invoice-discounts-card")
      .getByRole("button", { name: `Remove discount ${couponName}` })
      .click();

    await expect(page.getByText("-$0.00")).not.toBeVisible();
  });

  test("Add invoice tax", async ({ page, context }) => {
    const taxRateName = `VAT 10% ${faker.string.alphanumeric({ length: 4 })}`;
    await context.request.post("/api/v1/tax-rates", {
      data: {
        name: taxRateName,
        percentage: 10,
      },
    });

    await page
      .getByTestId("invoice-taxes-card")
      .getByRole("button", { name: "Add tax" })
      .click();
    await page.getByRole("option", { name: taxRateName }).click();

    await expect(page.getByText(`${taxRateName}10 %`)).toBeVisible();
    await expect(page.getByText("$0.00")).toBeVisible();
  });

  test("Remove invoice tax", async ({ page, context }) => {
    const taxRateName = `VAT 10% ${faker.string.alphanumeric({ length: 4 })}`;
    await context.request.post("/api/v1/tax-rates", {
      data: {
        name: taxRateName,
        percentage: 10,
      },
    });

    await page
      .getByTestId("invoice-taxes-card")
      .getByRole("button", { name: "Add tax" })
      .click();
    await page.getByRole("option", { name: taxRateName }).click();

    await expect(page.getByText("$0.00")).toBeVisible();
    await page
      .getByTestId("invoice-taxes-card")
      .getByRole("button", { name: `Remove tax ${taxRateName}` })
      .click();

    await expect(page.getByText("$0.00")).not.toBeVisible();
  });
});
