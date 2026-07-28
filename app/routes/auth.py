from __future__ import annotations

import hashlib
import secrets
import smtplib
import ssl
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from app.config import settings
from app.database import get_connection
from app.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


RESET_TOKEN_EXPIRY_MINUTES = 30

GENERIC_RESET_MESSAGE = (
    "If an account exists for that email address, "
    "password reset instructions have been sent."
)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        min_length=32,
        max_length=500,
    )
    new_password: str = Field(
        min_length=12,
        max_length=128,
    )


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")

    if forwarded:
        return forwarded.split(",", 1)[0].strip()

    if request.client:
        return request.client.host

    return None


def validate_new_password(password: str) -> None:
    has_uppercase = any(
        character.isupper() for character in password
    )
    has_lowercase = any(
        character.islower() for character in password
    )
    has_number = any(
        character.isdigit() for character in password
    )
    has_special = any(
        not character.isalnum() for character in password
    )

    if not has_uppercase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Password must include at least one "
                "uppercase letter."
            ),
        )

    if not has_lowercase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Password must include at least one "
                "lowercase letter."
            ),
        )

    if not has_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must include at least one number.",
        )

    if not has_special:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Password must include at least one "
                "special character."
            ),
        )


def build_reset_url(token: str) -> str:
    frontend_url = str(
        getattr(
            settings,
            "frontend_url",
            "http://localhost:3000",
        )
    ).rstrip("/")

    return f"{frontend_url}/reset-password?token={token}"


def send_password_reset_email(
    recipient: str,
    full_name: str,
    reset_url: str,
) -> None:
    smtp_host = str(
        getattr(settings, "smtp_host", "")
    ).strip()

    smtp_port = int(
        getattr(settings, "smtp_port", 587)
    )

    smtp_username = str(
        getattr(settings, "smtp_username", "")
    ).strip()

    smtp_password = str(
        getattr(settings, "smtp_password", "")
    )

    smtp_from_email = str(
        getattr(
            settings,
            "smtp_from_email",
            smtp_username,
        )
    ).strip()

    smtp_from_name = str(
        getattr(
            settings,
            "smtp_from_name",
            "Makwande Careers",
        )
    ).strip()

    smtp_use_tls = bool(
        getattr(settings, "smtp_use_tls", True)
    )

    if not smtp_host:
        raise RuntimeError(
            "SMTP_HOST has not been configured."
        )

    if not smtp_from_email:
        raise RuntimeError(
            "SMTP_FROM_EMAIL has not been configured."
        )

    message = EmailMessage()
    message["Subject"] = "Reset your Makwande Careers password"
    message["From"] = (
        f"{smtp_from_name} <{smtp_from_email}>"
    )
    message["To"] = recipient

    safe_name = full_name.strip() or "Makwande Careers member"

    message.set_content(
        f"""Hello {safe_name},

We received a request to reset your Makwande Careers password.

Use the secure link below to create a new password:

{reset_url}

This link will expire in {RESET_TOKEN_EXPIRY_MINUTES} minutes and can only be used once.

If you did not request a password reset, you can safely ignore this email.

Regards,
Makwande Careers
"""
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
      <body style="
        font-family: Arial, sans-serif;
        background: #f5f7fa;
        margin: 0;
        padding: 30px;
      ">
        <div style="
          max-width: 600px;
          margin: auto;
          background: white;
          padding: 32px;
          border-radius: 12px;
        ">
          <h2>Reset your password</h2>

          <p>Hello {safe_name},</p>

          <p>
            We received a request to reset your
            Makwande Careers password.
          </p>

          <p style="margin: 30px 0;">
            <a
              href="{reset_url}"
              style="
                background: #111827;
                color: white;
                padding: 14px 22px;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
              "
            >
              Reset password
            </a>
          </p>

          <p>
            This link expires in
            {RESET_TOKEN_EXPIRY_MINUTES} minutes
            and can only be used once.
          </p>

          <p>
            If you did not request this change,
            you can safely ignore this email.
          </p>

          <p>Regards,<br>Makwande Careers</p>
        </div>
      </body>
    </html>
    """

    message.add_alternative(
        html_content,
        subtype="html",
    )

    context = ssl.create_default_context()

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=30,
    ) as smtp:
        smtp.ehlo()

        if smtp_use_tls:
            smtp.starttls(context=context)
            smtp.ehlo()

        if smtp_username:
            smtp.login(
                smtp_username,
                smtp_password,
            )

        smtp.send_message(message)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest):
    email = normalize_email(payload.email)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM users
                WHERE email = %s
                """,
                (email,),
            )

            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )

            cursor.execute(
                """
                INSERT INTO users (
                    id,
                    email,
                    full_name,
                    password_hash
                )
                VALUES (%s, %s, %s, %s)
                RETURNING
                    id,
                    email,
                    full_name,
                    role,
                    is_active,
                    created_at
                """,
                (
                    str(uuid4()),
                    email,
                    payload.full_name.strip(),
                    hash_password(payload.password),
                ),
            )

            user = cursor.fetchone()

        connection.commit()

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    request: Request,
):
    email = normalize_email(payload.email)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,),
            )

            user = cursor.fetchone()

    if not user or not verify_password(
        payload.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token = create_token(
        str(user["id"]),
        user["role"],
    )

    token_payload = decode_token(access_token)
    ip_address = get_client_ip(request)
    user_agent = request.headers.get(
        "user-agent",
        "",
    )[:1000]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_sessions (
                    id,
                    user_id,
                    token_jti,
                    user_agent,
                    ip_address,
                    expires_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    user["id"],
                    token_payload["jti"],
                    user_agent,
                    ip_address,
                    datetime.fromtimestamp(
                        token_payload["exp"],
                        UTC,
                    ),
                ),
            )

            cursor.execute(
                """
                INSERT INTO security_events (
                    id,
                    user_id,
                    event_type,
                    ip_address,
                    user_agent
                )
                VALUES (%s, %s, 'login', %s, %s)
                """,
                (
                    str(uuid4()),
                    user["id"],
                    ip_address,
                    user_agent,
                ),
            )

        connection.commit()

    return TokenResponse(
        access_token=access_token,
    )


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
):
    email = normalize_email(payload.email)
    user = None

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, full_name, is_active
                FROM users
                WHERE email = %s
                """,
                (email,),
            )

            user = cursor.fetchone()

    if not user or not user["is_active"]:
        return {
            "message": GENERIC_RESET_MESSAGE,
        }

    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_reset_token(raw_token)

    expires_at = datetime.now(UTC) + timedelta(
        minutes=RESET_TOKEN_EXPIRY_MINUTES
    )

    reset_token_id = str(uuid4())

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM password_reset_tokens
                WHERE user_id = %s
                   OR expires_at <= NOW()
                   OR used_at IS NOT NULL
                """,
                (user["id"],),
            )

            cursor.execute(
                """
                INSERT INTO password_reset_tokens (
                    id,
                    user_id,
                    token_hash,
                    expires_at
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    reset_token_id,
                    user["id"],
                    token_hash,
                    expires_at,
                ),
            )

        connection.commit()

    reset_url = build_reset_url(raw_token)

    try:
        send_password_reset_email(
            recipient=user["email"],
            full_name=user["full_name"],
            reset_url=reset_url,
        )
    except Exception as error:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM password_reset_tokens
                    WHERE id = %s
                    """,
                    (reset_token_id,),
                )

            connection.commit()

        print(
            "Password reset email failed:",
            repr(error),
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Password reset email service is temporarily "
                "unavailable. Please try again later."
            ),
        ) from error

    ip_address = get_client_ip(request)
    user_agent = request.headers.get(
        "user-agent",
        "",
    )[:1000]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO security_events (
                    id,
                    user_id,
                    event_type,
                    ip_address,
                    user_agent
                )
                VALUES (
                    %s,
                    %s,
                    'password_reset_requested',
                    %s,
                    %s
                )
                """,
                (
                    str(uuid4()),
                    user["id"],
                    ip_address,
                    user_agent,
                ),
            )

        connection.commit()

    return {
        "message": GENERIC_RESET_MESSAGE,
    }


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
):
    validate_new_password(payload.new_password)

    supplied_token_hash = hash_reset_token(
        payload.token.strip()
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    password_reset_tokens.id,
                    password_reset_tokens.user_id,
                    password_reset_tokens.expires_at,
                    password_reset_tokens.used_at,
                    users.password_hash,
                    users.is_active
                FROM password_reset_tokens
                INNER JOIN users
                    ON users.id = password_reset_tokens.user_id
                WHERE password_reset_tokens.token_hash = %s
                FOR UPDATE
                """,
                (supplied_token_hash,),
            )

            reset_record = cursor.fetchone()

            if not reset_record:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "This password reset link is invalid "
                        "or has already been used."
                    ),
                )

            if reset_record["used_at"] is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "This password reset link has already "
                        "been used."
                    ),
                )

            if reset_record["expires_at"] <= datetime.now(UTC):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "This password reset link has expired. "
                        "Request a new one."
                    ),
                )

            if not reset_record["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is disabled.",
                )

            if verify_password(
                payload.new_password,
                reset_record["password_hash"],
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Your new password must be different "
                        "from your current password."
                    ),
                )

            cursor.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
                """,
                (
                    hash_password(payload.new_password),
                    reset_record["user_id"],
                ),
            )

            cursor.execute(
                """
                UPDATE password_reset_tokens
                SET used_at = NOW()
                WHERE id = %s
                """,
                (reset_record["id"],),
            )

            cursor.execute(
                """
                UPDATE password_reset_tokens
                SET used_at = NOW()
                WHERE user_id = %s
                  AND used_at IS NULL
                """,
                (reset_record["user_id"],),
            )

            cursor.execute(
                """
                DELETE FROM user_sessions
                WHERE user_id = %s
                """,
                (reset_record["user_id"],),
            )

            cursor.execute(
                """
                INSERT INTO security_events (
                    id,
                    user_id,
                    event_type,
                    ip_address,
                    user_agent
                )
                VALUES (
                    %s,
                    %s,
                    'password_reset_completed',
                    %s,
                    %s
                )
                """,
                (
                    str(uuid4()),
                    reset_record["user_id"],
                    get_client_ip(request),
                    request.headers.get(
                        "user-agent",
                        "",
                    )[:1000],
                ),
            )

        connection.commit()

    return {
        "message": (
            "Your password has been reset successfully. "
            "You can now sign in with your new password."
        ),
    }