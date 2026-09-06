import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from jwt.exceptions import InvalidTokenError, PyJWKError

from app.config import settings


class OidcError(ValueError):
    pass


class OidcService:
    async def authorization_url(self, redirect_uri: str) -> tuple[str, str]:
        configuration = await self._configuration()
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        challenge = self._base64url(hashlib.sha256(verifier.encode()).digest())
        now = datetime.now(timezone.utc)
        transaction = jwt.encode(
            {
                "state": state,
                "nonce": nonce,
                "verifier": verifier,
                "redirect_uri": redirect_uri,
                "iat": now,
                "exp": now + timedelta(minutes=10),
                "type": "oidc_transaction",
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        query = urlencode(
            {
                "response_type": "code",
                "client_id": settings.OIDC_CLIENT_ID,
                "redirect_uri": redirect_uri,
                "scope": settings.OIDC_SCOPES,
                "state": state,
                "nonce": nonce,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        return f"{configuration['authorization_endpoint']}?{query}", transaction

    async def authenticate_callback(
        self,
        *,
        code: str,
        state: str,
        transaction_token: str,
    ) -> dict:
        transaction = self._decode_transaction(transaction_token)
        if not hmac.compare_digest(transaction["state"], state):
            raise OidcError("OIDC state validation failed.")
        configuration = await self._configuration()
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            token_response = await client.post(
                configuration["token_endpoint"],
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": transaction["redirect_uri"],
                    "client_id": settings.OIDC_CLIENT_ID,
                    "client_secret": settings.OIDC_CLIENT_SECRET,
                    "code_verifier": transaction["verifier"],
                },
            )
            token_response.raise_for_status()
            tokens = token_response.json()
            id_token = tokens.get("id_token")
            if not id_token:
                raise OidcError("The identity provider did not return an ID token.")
            jwks_response = await client.get(configuration["jwks_uri"])
            jwks_response.raise_for_status()

        header = jwt.get_unverified_header(id_token)
        allowed_algorithms = {
            value.strip()
            for value in settings.OIDC_ALLOWED_ALGORITHMS.split(",")
            if value.strip()
        }
        if header.get("alg") not in allowed_algorithms:
            raise OidcError("OIDC signing algorithm is not allowed.")
        signing_key = next(
            (
                key
                for key in jwks_response.json().get("keys", [])
                if key.get("kid") == header.get("kid")
            ),
            None,
        )
        if signing_key is None:
            raise OidcError("The OIDC signing key is unavailable.")
        try:
            verification_key = jwt.PyJWK.from_dict(
                signing_key,
                algorithm=header["alg"],
            )
            claims = jwt.decode(
                id_token,
                verification_key,
                algorithms=[header["alg"]],
                audience=settings.OIDC_CLIENT_ID,
                issuer=configuration["issuer"],
            )
            self._validate_access_token_hash(
                claims,
                header["alg"],
                tokens.get("access_token"),
            )
        except (InvalidTokenError, PyJWKError, KeyError, ValueError) as exc:
            raise OidcError("OIDC ID token validation failed.") from exc
        if not hmac.compare_digest(str(claims.get("nonce", "")), transaction["nonce"]):
            raise OidcError("OIDC nonce validation failed.")
        if not claims.get("sub") or not claims.get("email"):
            raise OidcError("OIDC subject and email claims are required.")
        return claims

    async def _configuration(self) -> dict:
        self._require_configuration()
        issuer = settings.OIDC_ISSUER_URL.rstrip("/")
        url = f"{issuer}/.well-known/openid-configuration"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                configuration = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcError("OIDC provider discovery failed.") from exc
        if configuration.get("issuer", "").rstrip("/") != issuer:
            raise OidcError("OIDC issuer discovery mismatch.")
        for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
            if not configuration.get(key):
                raise OidcError(f"OIDC discovery is missing {key}.")
        return configuration

    @staticmethod
    def _decode_transaction(token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            if payload.get("type") != "oidc_transaction":
                raise OidcError("Invalid OIDC transaction.")
            return payload
        except InvalidTokenError as exc:
            raise OidcError("Invalid or expired OIDC transaction.") from exc

    @staticmethod
    def _validate_access_token_hash(
        claims: dict,
        algorithm: str,
        access_token: str | None,
    ) -> None:
        """Validate the optional OIDC at_hash claim against the access token."""
        expected_hash = claims.get("at_hash")
        if expected_hash is None:
            return
        if not access_token:
            raise OidcError("OIDC access token required for at_hash validation.")
        digest = jwt.get_algorithm_by_name(algorithm).compute_hash_digest(
            access_token.encode()
        )
        actual_hash = base64.urlsafe_b64encode(
            digest[: len(digest) // 2]
        ).rstrip(b"=").decode()
        if not hmac.compare_digest(str(expected_hash), actual_hash):
            raise OidcError("OIDC access token hash validation failed.")

    @staticmethod
    def _require_configuration() -> None:
        if not settings.OIDC_ENABLED:
            raise OidcError("OIDC is disabled.")
        if not all(
            (
                settings.OIDC_ISSUER_URL,
                settings.OIDC_CLIENT_ID,
                settings.OIDC_CLIENT_SECRET,
            )
        ):
            raise OidcError("OIDC configuration is incomplete.")

    @staticmethod
    def _base64url(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode().rstrip("=")
