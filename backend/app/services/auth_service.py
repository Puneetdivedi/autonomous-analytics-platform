"""Authentication & token issuance service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair


class AuthService:
    """Handles registration, credential verification and JWT issuance."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def register(self, data: RegisterRequest) -> User:
        """Create a new user, hashing the password.

        Raises :class:`ConflictError` if the email is already registered.
        """
        existing = await self.users.get_by_email(str(data.email))
        if existing is not None:
            raise ConflictError(
                "Email already registered",
                details={"email": str(data.email)},
            )
        return await self.users.create(
            email=str(data.email),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
        )

    async def authenticate(self, email: str, password: str) -> User:
        """Return the user for valid credentials or raise
        :class:`AuthenticationError`."""
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        return user

    def _issue_tokens(self, user: User) -> TokenPair:
        access = create_access_token(user.id, role=user.role.value)
        refresh = create_refresh_token(user.id)
        return TokenPair(access_token=access, refresh_token=refresh)

    async def login(self, data: LoginRequest) -> TokenPair:
        """Authenticate credentials and return a fresh token pair."""
        user = await self.authenticate(str(data.email), data.password)
        return self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        """Validate a refresh token and issue a new token pair."""
        payload = decode_token(refresh_token, expected_type="refresh")
        subject = payload.get("sub")
        if not subject:
            raise AuthenticationError("Invalid refresh token")
        user = await self.users.get(subject)
        if user is None or not user.is_active:
            raise AuthenticationError("User no longer exists or is disabled")
        return self._issue_tokens(user)
