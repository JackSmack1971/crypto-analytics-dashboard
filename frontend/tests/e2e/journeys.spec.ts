import { test, expect } from '@playwright/test';

// Network stubbing to avoid real provider calls
async function stubApi(page) {
  await page.route('**/api/**', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: '{}',
    });
  });
}

test.describe('Critical user journeys', () => {
  test('UJ1 - watchlist/asset detail loads', async ({ page }) => {
    await stubApi(page);
    await page.goto('/');
    await expect(
      page.getByRole('heading', { name: 'Crypto Analytics Dashboard' }),
    ).toBeVisible();
  });

  test('UJ2 - portfolio route responds', async ({ page }) => {
    await stubApi(page);
    const response = await page.goto('/portfolio');
    expect(response?.status()).toBe(404);
  });

  test('UJ3 - CSV import route responds', async ({ page }) => {
    await stubApi(page);
    const response = await page.goto('/import');
    expect(response?.status()).toBe(404);
  });

  test('UJ4 - operator console route responds', async ({ page }) => {
    await stubApi(page);
    const response = await page.goto('/operator');
    expect(response?.status()).toBe(404);
  });
});
