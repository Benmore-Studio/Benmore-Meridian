import { test, expect } from '@playwright/test';

test('homepage loads successfully', async ({ page }) => {
  await page.goto('/');

  // Check that the page loaded
  await expect(page).toHaveTitle(/Home/);

  // Add more assertions based on your app
});

test('API integration works', async ({ page, request }) => {
  // Example: Test API call from the frontend
  await page.goto('/users');

  // Wait for API request to complete
  const response = await page.waitForResponse((resp) =>
    resp.url().includes('/api/users')
  );

  expect(response.status()).toBe(200);

  // Verify data is displayed
  await expect(page.locator('[data-testid="user-list"]')).toBeVisible();
});
