import { test, expect, Page } from '@playwright/test';

// Generate unique identifiers for each test run to avoid conflicts
const generate_unique_id = () => `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
const generate_test_email = () => `test_${generate_unique_id()}@example.com`;
const generate_test_username = () => `user_${generate_unique_id()}`;

// Helper to open sidebar on mobile (needed to access login)
async function open_sidebar_if_mobile(page: Page) {
  // Check if mobile navbar hamburger menu is visible
  const hamburger = page.getByTestId('btn-mobile-menu');
  if (await hamburger.isVisible({ timeout: 1000 }).catch(() => false)) {
    await hamburger.click();
    // Wait for sidebar to open
    await page.waitForTimeout(300);
  }
}

// Helper to click login and open modal (handles both desktop and mobile)
async function open_login_modal(page: Page) {
  await open_sidebar_if_mobile(page);

  // Try sidebar testid first (mobile), then button text (desktop home page)
  const sidebar_login = page.getByTestId('btn-open-login');
  if (await sidebar_login.isVisible({ timeout: 1000 }).catch(() => false)) {
    await sidebar_login.click();
  } else {
    await page.locator('button').filter({ hasText: /login/i }).first().click();
  }

  // Wait for modal to appear (login button visible means modal is open)
  await expect(page.getByTestId('btn-login')).toBeVisible({ timeout: 5000 });
}

test.describe('Authentication Flow', () => {
  test.describe('Signup', () => {
    test('should signup a new user successfully', async ({ page }) => {
      const test_email = generate_test_email();
      const test_username = generate_test_username();
      const test_password = 'TestPassword123!';

      // Navigate to signup page
      await page.goto('/signup');

      // Fill out the signup form
      await page.locator('#username').fill(test_username);
      await page.locator('#email').fill(test_email);
      await page.locator('#password').fill(test_password);
      await page.locator('#password-verify').fill(test_password);

      // Submit the form (wait for button to be enabled, then scroll and click)
      const submit_button = page.getByTestId("btn-signup-submit");
      await expect(submit_button).toBeEnabled({ timeout: 5000 });
      await submit_button.scrollIntoViewIfNeeded();
      await submit_button.click();

      // Should redirect to home page after successful signup
      await expect(page).toHaveURL('/', { timeout: 10000 });
    });

    test('should show error for duplicate email', async ({ page }) => {
      const test_email = generate_test_email();
      const test_password = 'TestPassword123!';

      // First signup
      await page.goto('/signup');
      await page.locator('#username').fill(generate_test_username());
      await page.locator('#email').fill(test_email);
      await page.locator('#password').fill(test_password);
      await page.locator('#password-verify').fill(test_password);
      const submit_button = page.getByTestId('btn-signup-submit');
      await expect(submit_button).toBeEnabled({ timeout: 5000 });
      await submit_button.scrollIntoViewIfNeeded();
      await submit_button.click();
      await expect(page).toHaveURL('/', { timeout: 10000 });

      // Logout (navigate to signup again as new session)
      await page.goto('/signup');

      // Second signup with same email
      await page.locator('#username').fill(generate_test_username());
      await page.locator('#email').fill(test_email);
      await page.locator('#password').fill(test_password);
      await page.locator('#password-verify').fill(test_password);
      const submit_button2 = page.getByTestId('btn-signup-submit');
      await expect(submit_button2).toBeEnabled({ timeout: 5000 });
      await submit_button2.scrollIntoViewIfNeeded();
      await submit_button2.click();

      // Should show error message about existing user
      await expect(page.getByTestId('error-email-exists')).toBeVisible();
    });

    test('should show error for password mismatch', async ({ page }) => {
      await page.goto('/signup');

      await page.locator('#username').fill('testuser');
      await page.locator('#email').fill(generate_test_email());
      await page.locator('#password').fill('Password123!');
      await page.locator('#password-verify').fill('DifferentPassword123!');

      // Error message should appear
      await expect(page.getByTestId('error-password-mismatch')).toBeVisible();

      // Submit button should be disabled
      await expect(page.getByTestId("btn-signup-submit")).toBeDisabled();
    });

    test('should show error for invalid email format', async ({ page }) => {
      await page.goto('/signup');

      await page.locator('#username').fill('testuser');
      await page.locator('#email').fill('invalid-email');
      await page.locator('#password').fill('Password123!');
      await page.locator('#password-verify').fill('Password123!');

      // Error message should appear
      await expect(page.getByTestId('error-invalid-email')).toBeVisible();
    });

    test('should show error for duplicate username', async ({ page }) => {
      const test_username = generate_test_username();
      const test_password = 'TestPassword123!';

      // First signup
      await page.goto('/signup');
      await page.locator('#username').fill(test_username);
      await page.locator('#email').fill(generate_test_email());
      await page.locator('#password').fill(test_password);
      await page.locator('#password-verify').fill(test_password);
      const submit_button = page.getByTestId('btn-signup-submit');
      await expect(submit_button).toBeEnabled({ timeout: 5000 });
      await submit_button.scrollIntoViewIfNeeded();
      await submit_button.click();
      await expect(page).toHaveURL('/', { timeout: 10000 });

      // Second signup with same username but different email
      await page.goto('/signup');
      await page.locator('#username').fill(test_username);
      await page.locator('#email').fill(generate_test_email());
      await page.locator('#password').fill(test_password);
      await page.locator('#password-verify').fill(test_password);
      const submit_button2 = page.getByTestId('btn-signup-submit');
      await expect(submit_button2).toBeEnabled({ timeout: 5000 });
      await submit_button2.scrollIntoViewIfNeeded();
      await submit_button2.click();

      // Should show error message about existing username
      await expect(page.getByTestId('error-username-exists')).toBeVisible({ timeout: 5000 });
    });

    test('should show error for username with profanity', async ({ page }) => {
      await page.goto('/signup');

      await page.locator('#username').fill('fucking_user');
      await page.locator('#email').fill(generate_test_email());
      await page.locator('#password').fill('Password123!');
      await page.locator('#password-verify').fill('Password123!');

      const submit_button = page.getByTestId('btn-signup-submit');
      await expect(submit_button).toBeEnabled({ timeout: 5000 });
      await submit_button.scrollIntoViewIfNeeded();
      await submit_button.click();

      // Should show error message about inappropriate language
      await expect(page.getByTestId('error-username-profanity')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Email Verification', () => {
    test('should verify email with token', async ({ page, request }) => {
      const test_email = generate_test_email();
      const test_username = generate_test_username();
      const test_password = 'TestPassword123!';

      // Signup first
      await page.goto('/signup');
      await page.locator('#username').fill(test_username);
      await page.locator('#email').fill(test_email);
      await page.locator('#password').fill(test_password);
      await page.locator('#password-verify').fill(test_password);
      const submit_button = page.getByTestId('btn-signup-submit');
      await expect(submit_button).toBeEnabled({ timeout: 5000 });
      await submit_button.scrollIntoViewIfNeeded();
      await submit_button.click();
      await expect(page).toHaveURL('/', { timeout: 10000 });

      // Get verification token from test API
      const token_response = await request.get(`/api/test/verification-token/${encodeURIComponent(test_email)}`);
      expect(token_response.ok()).toBeTruthy();
      const { token } = await token_response.json();

      // Visit verification URL
      await page.goto(`/verify-email?token=${token}`);

      // Should redirect to home with verified query param
      await expect(page).toHaveURL('/?verified=true');

      // Should see verification success message
      await expect(page.getByTestId('banner-email-successfully-verified')).toBeVisible()
    });

    test('should show error for invalid verification token', async ({ page }) => {
      // Visit verification URL with invalid token
      await page.goto('/verify-email?token=invalid-token-12345');

      // Should show error message
      await expect(page.getByTestId('error-verification')).toBeVisible({ timeout: 5000 });
    });

    test('should show already verified when using second token after first verification', async ({ page, request }) => {
      const test_email = generate_test_email();
      const test_username = generate_test_username();
      const test_password = 'TestPassword123!';

      // Signup first (same as 'should verify email with token')
      await page.goto('/signup');
      await page.locator('#username').fill(test_username);
      await page.locator('#email').fill(test_email);
      await page.locator('#password').fill(test_password);
      await page.locator('#password-verify').fill(test_password);
      const submit_button = page.getByTestId('btn-signup-submit');
      await expect(submit_button).toBeEnabled({ timeout: 5000 });
      await submit_button.scrollIntoViewIfNeeded();
      await submit_button.click();
      await expect(page).toHaveURL('/', { timeout: 10000 });

      // Get first verification token from test API
      const token1_response = await request.get(`/api/test/verification-token/${encodeURIComponent(test_email)}`);
      expect(token1_response.ok()).toBeTruthy();
      const { token: token1 } = await token1_response.json();

      // Request resend verification email (user is already logged in from signup)
      await request.post('/api/auth/request-verify-token');

      // Get second verification token
      const token2_response = await request.get(`/api/test/verification-token/${encodeURIComponent(test_email)}`);
      expect(token2_response.ok()).toBeTruthy();
      const { token: token2 } = await token2_response.json();

      // Verify with first token - should succeed
      await page.goto(`/verify-email?token=${token1}`);
      await expect(page).toHaveURL('/?verified=true', { timeout: 10000 });

      // Verify with second token - should show already verified
      await page.goto(`/verify-email?token=${token2}`);
      await expect(page).toHaveURL(/alreadyVerified=true/, { timeout: 10000 });

      // Should see already verified banner
      await expect(page.getByTestId('banner-email-already-verified')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Login', () => {
    test('should login successfully', async ({ page, request }) => {
      const test_email = generate_test_email();
      const test_username = generate_test_username();
      const test_password = 'TestPassword123!';

      // Register user via API first
      await request.post('/api/auth/register', {
        data: {
          username: test_username,
          email: test_email,
          password: test_password,
        },
      });

      await page.goto('/');

      // Open login modal (handles mobile sidebar)
      await open_login_modal(page);

      // Fill login form
      await page.locator('#email').fill(test_email);
      await page.locator('#password').fill(test_password);

      // Submit login
      const submit_button = page.getByTestId('btn-login');
      await expect(submit_button).toBeEnabled({ timeout: 5000 });
      await submit_button.click();

      // Modal should close and user should be logged in
      await expect(page.getByTestId('btn-login')).not.toBeVisible({ timeout: 5000 });

      // Verify user menu is visible (indicates logged in state)
      await open_sidebar_if_mobile(page);
      await expect(page.getByTestId('sidebar-user-menu')).toBeVisible({ timeout: 5000 });
    });

    test('should show error for bad credentials', async ({ page, request }) => {
      const test_email = generate_test_email();
      const test_username = generate_test_username();
      const test_password = 'TestPassword123!';

      // Register user via API first
      await request.post('/api/auth/register', {
        data: {
          username: test_username,
          email: test_email,
          password: test_password,
        },
      });

      await page.goto('/');

      // Open login modal
      await open_login_modal(page);

      // Fill with wrong password
      await page.locator('#email').fill(test_email);
      await page.locator('#password').fill('WrongPassword123!');

      // Submit login
      const submit_button = page.getByTestId('btn-login');
      await expect(submit_button).toBeEnabled({ timeout: 5000 });
      await submit_button.click();

      // Should show error message
      await expect(page.getByTestId('error-login-bad-credentials')).toBeVisible({ timeout: 5000 });
    });

    test('should navigate to signup from login modal', async ({ page }) => {
      await page.goto('/');

      // Open login modal
      await open_login_modal(page);

      // Click signup link in modal
      await page.getByTestId('link-signup').click();

      // Should navigate to signup page
      await expect(page).toHaveURL('/signup', { timeout: 5000 });
    });
  });

  test.describe('Logout', () => {
    test('should logout successfully', async ({ page, request }) => {
      const test_email = generate_test_email();
      const test_username = generate_test_username();
      const test_password = 'TestPassword123!';

      // Register user via API
      await request.post('/api/auth/register', {
        data: {
          username: test_username,
          email: test_email,
          password: test_password,
        },
      });

      // Login via UI
      await page.goto('/');
      await open_login_modal(page);
      await page.locator('#email').fill(test_email);
      await page.locator('#password').fill(test_password);
      const login_button = page.getByTestId('btn-login');
      await expect(login_button).toBeEnabled({ timeout: 5000 });
      await login_button.click();

      // Wait for login to complete (modal closes)
      await expect(page.getByTestId('btn-login')).not.toBeVisible({ timeout: 5000 });

      // Open sidebar on mobile to access user menu
      await open_sidebar_if_mobile(page);

      // Open user dropdown menu and click logout
      await page.getByTestId('sidebar-user-menu').click();
      await page.getByTestId('btn-logout').click();

      // Should show login option again (user is logged out)
      await page.goto('/');
      await open_sidebar_if_mobile(page);

      // Verify user menu is NOT visible (logged out state)
      await expect(page.getByTestId('sidebar-user-menu')).not.toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Password Reset', () => {
    test('should complete full password reset flow', async ({ page, request }) => {
      const test_email = generate_test_email();
      const test_username = generate_test_username();
      const old_password = 'OldPassword123!';
      const new_password = 'NewPassword456!';

      // Register user via API first
      await request.post('/api/auth/register', {
        data: {
          username: test_username,
          email: test_email,
          password: old_password,
        },
      });

      // Go to home and open login modal
      await page.goto('/');
      await open_login_modal(page);

      // Click forgot password link
      await page.getByTestId('link-forgot-password').click();

      // Should show forgot password dialog (check for email input)
      await expect(page.locator('#forgot-email')).toBeVisible({ timeout: 5000 });

      // Enter email and submit
      await page.locator('#forgot-email').fill(test_email);
      const forgot_submit = page.getByTestId('btn-forgot-password-submit');
      await expect(forgot_submit).toBeEnabled({ timeout: 5000 });
      await forgot_submit.click();

      // Should show success message
      await expect(page.getByTestId('forgot-password-success')).toBeVisible({ timeout: 5000 });

      // Get reset token from test API
      const token_response = await request.get(`/api/test/reset-token/${encodeURIComponent(test_email)}`);
      expect(token_response.ok()).toBeTruthy();
      const { token } = await token_response.json();

      // Navigate to reset password page with token
      await page.goto(`/reset-password?token=${token}`);

      // Fill in new password
      await page.locator('#new-password').fill(new_password);
      await page.locator('#confirm-password').fill(new_password);

      // Submit reset
      const reset_submit = page.getByTestId('btn-reset-password-submit');
      await expect(reset_submit).toBeEnabled({ timeout: 5000 });
      await reset_submit.click();

      // Should show success message
      await expect(page.getByTestId('reset-password-success')).toBeVisible({ timeout: 5000 });

      // Wait for redirect to home with login modal (3 seconds in the app)
      await expect(page).toHaveURL('/', { timeout: 5000 });
      await expect(page.getByTestId('btn-login')).toBeVisible({ timeout: 5000 });

      // Login with new password
      await page.locator('#email').fill(test_email);
      await page.locator('#password').fill(new_password);
      const login_button = page.getByTestId('btn-login');
      await expect(login_button).toBeEnabled({ timeout: 5000 });
      await login_button.click();

      // Should be logged in (modal closes, user menu visible)
      await expect(page.getByTestId('btn-login')).not.toBeVisible({ timeout: 5000 });
      await open_sidebar_if_mobile(page);
      await expect(page.getByTestId('sidebar-user-menu')).toBeVisible({ timeout: 5000 });
    });

    test('should show error for invalid reset token', async ({ page }) => {
      // Navigate to reset password page with invalid token
      await page.goto('/reset-password?token=invalid-token-12345');

      // Fill in passwords
      await page.locator('#new-password').fill('NewPassword123!');
      await page.locator('#confirm-password').fill('NewPassword123!');

      // Submit reset
      const reset_submit = page.getByTestId('btn-reset-password-submit');
      await expect(reset_submit).toBeEnabled({ timeout: 5000 });
      await reset_submit.click();

      // Should show error message
      await expect(page.getByTestId('error-bad-token')).toBeVisible({ timeout: 5000 });
    });

    test('should show error for missing reset token', async ({ page }) => {
      await page.goto('/reset-password'); // Navigate to reset password page without token
      await expect(page.getByTestId('error-bad-token')).toBeVisible({ timeout: 5000 });  // Should show error message immediately
      await expect(page.getByTestId('btn-reset-password-submit')).toBeDisabled(); // Submit button should be disabled
    });
  });
});
