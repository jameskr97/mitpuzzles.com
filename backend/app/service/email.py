import resend
from fastapi import HTTPException

from app.config import settings

# Store tokens in test mode for retrieval by test endpoints
_test_verification_tokens: dict[str, str] = {}  # email -> token
_test_reset_tokens: dict[str, str] = {}  # email -> token


def get_test_verification_token(email: str) -> str | None:
    """Retrieve stored verification token for email (test mode only)"""
    return _test_verification_tokens.get(email)


def get_test_reset_token(email: str) -> str | None:
    """Retrieve stored password reset token for email (test mode only)"""
    return _test_reset_tokens.get(email)

VERIFICATION_EMAIL_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Verify Your Email - MIT Puzzles</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="bg-gray-100">
    <div class="mx-auto my-10 max-w-lg overflow-hidden rounded-lg border bg-white shadow-lg">
      <!-- Body -->
      <div class="space-y-4 p-8">
        <p class="text-lg text-gray-700">Hey {{USERNAME}}! You just signed up at <span class="font-semibold">mitpuzzles.com</span></p>

        <p class="text-gray-600">Please click the link below to verify your email address and complete your registration:</p>

        <!-- CTA Button -->
        <div class="py-4 text-center">
          <a href="{{VERIFICATION_LINK}}" class="inline-block rounded-lg bg-blue-600 px-3 py-2 text-lg font-bold text-white transition-colors duration-200 hover:bg-blue-700"> Verify Email Address </a>
        </div>

        <!-- Alternative link -->
        <div class="space-y-2 text-sm text-gray-500">
          <p>Or copy and paste this link into your browser:</p>
          <p class="rounded bg-gray-100 p-2 font-mono text-xs break-all">{{VERIFICATION_LINK}}</p>
        </div>

        <!-- Footer note -->
        <div class="mt-6 border-t border-gray-200 pt-4">
          <p class="text-sm text-gray-500">If you didn't sign up for MIT Puzzles, you can safely ignore this email.</p>
        </div>
      </div>
    </div>
  </body>
</html>
"""

VERIFICATION_EMAIL_PLAINTEXT = """Hey {{USERNAME}}!

You just signed up at mitpuzzles.com.
Please verify your email by clicking this link:

{{VERIFICATION_LINK}}

This link will expire in 24 hours.

If you didn't sign up for MIT Puzzles, you can safely ignore this email.
"""


async def send_verification_email(to_email: str, verification_token: str, base_url: str = "https://mitpuzzles.com") -> bool:
    """Send verification email using Resend with file templates"""

    # In test mode, store token and skip actual email sending
    if settings.TESTING:
        _test_verification_tokens[to_email] = verification_token
        print(f"[TEST MODE] Verification token stored for {to_email}")
        return True

    verification_link = f"{base_url}/verify-email?token={verification_token}"

    try:
        html_content = VERIFICATION_EMAIL_HTML.replace("{{USERNAME}}", to_email).replace("{{VERIFICATION_LINK}}", verification_link)

        text_content = VERIFICATION_EMAIL_PLAINTEXT.replace("{{USERNAME}}", to_email).replace("{{VERIFICATION_LINK}}", verification_link)

        # send email via resend
        response = resend.Emails.send(
            {
                "from": "MITPuzzles <noreply@mitpuzzles.com>",
                "to": [to_email],
                "subject": "Verify your email for MIT Puzzles",
                "html": html_content,
                "text": text_content,
            },
            resend.Emails.SendOptions(idempotency_key=verification_token[:256]),
        )

        print(f"Email sent successfully: {response}")
        return True

    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send verification email")


async def send_password_reset_email(to_email: str, reset_token: str, base_url: str = "https://mitpuzzles.com") -> bool:
    """Send password reset email using Resend"""

    # In test mode, store token and skip actual email sending
    if settings.TESTING:
        _test_reset_tokens[to_email] = reset_token
        print(f"[TEST MODE] Password reset token stored for {to_email}")
        return True

    reset_link = f"{base_url}/reset-password?token={reset_token}"

    html_template = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Reset Your Password - MIT Puzzles</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="bg-gray-100">
    <div class="mx-auto my-10 max-w-lg overflow-hidden rounded-lg border bg-white shadow-lg">
      <div class="space-y-4 p-8">
        <p class="text-lg text-gray-700">You requested to reset your password on <span class="font-semibold">mitpuzzles.com</span></p>

        <p class="text-gray-600">Click the button below to reset your password:</p>

        <div class="py-4 text-center">
          <a href="{{RESET_LINK}}" class="inline-block rounded-lg bg-blue-600 px-3 py-2 text-lg font-bold text-white transition-colors duration-200 hover:bg-blue-700"> Reset Password </a>
        </div>

        <div class="space-y-2 text-sm text-gray-500">
          <p>Or copy and paste this link into your browser:</p>
          <p class="rounded bg-gray-100 p-2 font-mono text-xs break-all">{{RESET_LINK}}</p>
        </div>

        <div class="mt-6 border-t border-gray-200 pt-4">
          <p class="text-sm text-gray-500">This link will expire in 1 hour.</p>
          <p class="text-sm text-gray-500 mt-2">If you didn't request a password reset, you can safely ignore this email.</p>
        </div>
      </div>
    </div>
  </body>
</html>
"""

    text_template = """You requested to reset your password on mitpuzzles.com.

Click this link to reset your password:

{{RESET_LINK}}

This link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email.
"""

    try:
        html_content = html_template.replace("{{RESET_LINK}}", reset_link)
        text_content = text_template.replace("{{RESET_LINK}}", reset_link)

        response = resend.Emails.send(
            {
                "from": "MITPuzzles <noreply@mitpuzzles.com>",
                "to": [to_email],
                "subject": "Reset your password for MIT Puzzles",
                "html": html_content,
                "text": text_content,
            },
            resend.Emails.SendOptions(idempotency_key=reset_token[:256]),
        )

        print(f"Password reset email sent successfully: {response}")
        return True

    except Exception as e:
        print(f"Failed to send password reset email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send password reset email")
