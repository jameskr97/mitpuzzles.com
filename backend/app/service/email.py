import resend
from fastapi import HTTPException

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
