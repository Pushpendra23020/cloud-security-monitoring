from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_mfa_challenge_token,
    decode_access_token,
    decode_mfa_challenge_token,
    hash_password,
    verify_password,
)
from app.database.models.audit_log import AuditLog
from app.database.session import get_db, set_tenant_context
from app.dependencies import CurrentTenant
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.auth import (
    AuthStatusResponse,
    AuthSessionResponse,
    LoginResponse,
    LoginRequest,
    MfaChallengeRequest,
    MfaCodeRequest,
    MfaDisableRequest,
    MfaSetupResponse,
    MfaStatusResponse,
    OrganizationAccessResponse,
    OrganizationSwitchRequest,
    TokenResponse,
    RecoveryCodesResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_session_service import (
    AuthSessionService,
    RefreshTokenReuseError,
    SessionAuthenticationError,
)
from app.services.auth_rate_limit_service import (
    AuthenticationRateLimitService,
    RateLimitExceeded,
)
from app.services.mfa_service import MfaError, MfaService
from app.services.oidc_service import OidcError, OidcService
from app.utils.client_ip import resolve_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])
DUMMY_PASSWORD_HASH = hash_password("Invalid-account-password-123!")


def _cookie_is_secure() -> bool:
    if settings.AUTH_COOKIE_SECURE is not None:
        return settings.AUTH_COOKIE_SECURE
    return settings.ENVIRONMENT.lower() == "production"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.AUTH_SESSION_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=_cookie_is_secure(),
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        httponly=True,
        secure=_cookie_is_secure(),
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/api/v1/auth",
    )


def _set_oidc_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.OIDC_TRANSACTION_COOKIE_NAME,
        value=token,
        max_age=600,
        httponly=True,
        secure=_cookie_is_secure(),
        samesite="lax",
        path="/api/v1/auth/oidc",
    )


def _clear_oidc_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.OIDC_TRANSACTION_COOKIE_NAME,
        httponly=True,
        secure=_cookie_is_secure(),
        samesite="lax",
        path="/api/v1/auth/oidc",
    )


def _issue_access_token(user, membership, session_id: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(
            user.id,
            user.username,
            membership.role,
            membership.organization_id,
            membership.id,
            session_id,
        ),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _client_ip(request: Request) -> str:
    return resolve_client_ip(request)


def _enforce_rate_limit(
    service: AuthenticationRateLimitService,
    *,
    client_ip: str,
    principal: str,
) -> None:
    try:
        service.ensure_allowed(client_ip=client_ip, principal=principal)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Try again later.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


def _complete_login(
    *,
    user,
    membership,
    request: Request,
    response: Response,
    db: Session,
    audit_action: str,
) -> TokenResponse:
    UserRepository(db).record_login(user)
    session, refresh_token = AuthSessionService(db).create(
        user_id=user.id,
        organization_id=membership.organization_id,
        membership_id=membership.id,
        user_agent=request.headers.get("User-Agent"),
        client_ip=_client_ip(request),
    )
    _set_refresh_cookie(response, refresh_token)
    _record_auth_audit(
        db,
        organization_id=membership.organization_id,
        username=user.username,
        action=audit_action,
        request=request,
    )
    return _issue_access_token(user, membership, session.id)


def _record_auth_audit(
    db: Session,
    *,
    organization_id: int,
    username: str,
    action: str,
    request: Request,
) -> None:
    set_tenant_context(db, organization_id)
    db.add(
        AuditLog(
            organization_id=organization_id,
            action=action,
            user=username,
            method=request.method,
            path=request.url.path,
            status_code=200,
            client_ip=resolve_client_ip(request),
        )
    )
    db.commit()


@router.get("/status", response_model=AuthStatusResponse)
def auth_status() -> AuthStatusResponse:
    return AuthStatusResponse(
        enabled=settings.AUTH_ENABLED,
        oidc_enabled=settings.OIDC_ENABLED,
        oidc_login_url=(
            "/api/v1/auth/oidc/start" if settings.OIDC_ENABLED else None
        ),
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse | TokenResponse:
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is disabled.",
        )
    repository = UserRepository(db)
    client_ip = _client_ip(request)
    rate_limits = AuthenticationRateLimitService(db)
    _enforce_rate_limit(
        rate_limits,
        client_ip=client_ip,
        principal=payload.username,
    )
    user = repository.get_by_username(payload.username)
    password_valid = verify_password(
        payload.password,
        user.password_hash if user is not None else DUMMY_PASSWORD_HASH,
    )
    if user is not None and not password_valid and not repository.is_locked(user):
        repository.record_failed_login(user)
    if (
        user is None
        or not user.is_active
        or repository.is_locked(user)
        or not password_valid
    ):
        rate_limits.record_failure(
            client_ip=client_ip,
            principal=payload.username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    organization_repository = OrganizationRepository(db)
    membership = organization_repository.get_default_membership(user.id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active organization membership.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    rate_limits.clear_principal(client_ip=client_ip, principal=payload.username)
    if user.mfa_enabled:
        challenge = MfaService(db).create_challenge(user.id)
        return LoginResponse(
            mfa_required=True,
            challenge_token=create_mfa_challenge_token(
                challenge.id,
                user.id,
                membership.organization_id,
                membership.id,
            ),
        )
    return _complete_login(
        user=user,
        membership=membership,
        request=request,
        response=response,
        db=db,
        audit_action="AUTH_LOGIN",
    )


@router.post("/mfa/verify", response_model=TokenResponse)
def verify_mfa_challenge(
    payload: MfaChallengeRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    client_ip = _client_ip(request)
    rate_limits = AuthenticationRateLimitService(db)
    try:
        challenge = decode_mfa_challenge_token(payload.challenge_token)
        user_id = int(challenge["sub"])
        organization_id = int(challenge["org_id"])
        membership_id = int(challenge["membership_id"])
        challenge_id = str(challenge["jti"])
    except (TokenError, TypeError, ValueError, KeyError) as exc:
        rate_limits.record_failure(client_ip=client_ip, principal="mfa:invalid")
        raise HTTPException(status_code=401, detail="Invalid or expired MFA challenge.") from exc

    principal = f"mfa:{user_id}"
    _enforce_rate_limit(rate_limits, client_ip=client_ip, principal=principal)
    user = UserRepository(db).get_by_id(user_id)
    membership = OrganizationRepository(db).get_membership(user_id, organization_id)
    mfa = MfaService(db)
    stored_challenge = mfa.lock_active_challenge(challenge_id, user_id)
    if (
        user is None
        or not user.is_active
        or membership is None
        or membership.id != membership_id
        or stored_challenge is None
        or not mfa.verify(user, payload.code, commit=False)
    ):
        rate_limits.record_failure(client_ip=client_ip, principal=principal)
        raise HTTPException(status_code=401, detail="Invalid authentication code.")
    rate_limits.clear_principal(client_ip=client_ip, principal=principal)
    mfa.consume_challenge(stored_challenge)
    return _complete_login(
        user=user,
        membership=membership,
        request=request,
        response=response,
        db=db,
        audit_action="AUTH_LOGIN_MFA",
    )


@router.get("/mfa/status", response_model=MfaStatusResponse)
def mfa_status(
    context: CurrentTenant,
    db: Session = Depends(get_db),
) -> MfaStatusResponse:
    return MfaStatusResponse(
        enabled=context.user.mfa_enabled,
        recovery_codes_remaining=MfaService(db).recovery_codes_remaining(
            context.user.id
        ),
    )


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def setup_mfa(
    context: CurrentTenant,
    db: Session = Depends(get_db),
) -> MfaSetupResponse:
    try:
        secret, uri = MfaService(db).begin_setup(context.user)
    except MfaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MfaSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/mfa/enable", response_model=RecoveryCodesResponse)
def enable_mfa(
    payload: MfaCodeRequest,
    context: CurrentTenant,
    request: Request,
    db: Session = Depends(get_db),
) -> RecoveryCodesResponse:
    try:
        codes = MfaService(db).enable(context.user, payload.code)
    except MfaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    AuthSessionRepository(db).revoke_all_except(
        context.user.id,
        context.session_id,
        "mfa_enabled",
    )
    _record_auth_audit(
        db,
        organization_id=context.organization_id,
        username=context.user.username,
        action="AUTH_MFA_ENABLED",
        request=request,
    )
    return RecoveryCodesResponse(recovery_codes=codes)


@router.post("/mfa/recovery-codes", response_model=RecoveryCodesResponse)
def regenerate_recovery_codes(
    payload: MfaCodeRequest,
    context: CurrentTenant,
    db: Session = Depends(get_db),
) -> RecoveryCodesResponse:
    service = MfaService(db)
    if not service.verify(context.user, payload.code):
        raise HTTPException(status_code=400, detail="Invalid authentication code.")
    return RecoveryCodesResponse(
        recovery_codes=service.regenerate_recovery_codes(context.user)
    )


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
def disable_mfa(
    payload: MfaDisableRequest,
    context: CurrentTenant,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    if not verify_password(payload.password, context.user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid password.")
    service = MfaService(db)
    if not service.verify(context.user, payload.code):
        raise HTTPException(status_code=400, detail="Invalid authentication code.")
    service.disable(context.user)
    AuthSessionRepository(db).revoke_all_except(
        context.user.id,
        context.session_id,
        "mfa_disabled",
    )
    _record_auth_audit(
        db,
        organization_id=context.organization_id,
        username=context.user.username,
        action="AUTH_MFA_DISABLED",
        request=request,
    )


@router.get("/oidc/start", include_in_schema=False)
async def start_oidc(request: Request) -> RedirectResponse:
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=404, detail="OIDC login is disabled.")
    redirect_uri = settings.OIDC_REDIRECT_URI or str(
        request.url_for("oidc_callback")
    )
    try:
        authorization_url, transaction = await OidcService().authorization_url(
            redirect_uri
        )
    except OidcError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    response = RedirectResponse(authorization_url, status_code=302)
    _set_oidc_cookie(response, transaction)
    return response


@router.get("/oidc/callback", name="oidc_callback", include_in_schema=False)
async def oidc_callback(
    request: Request,
    code: str = Query(min_length=1, max_length=4096),
    state_value: str = Query(alias="state", min_length=16, max_length=1024),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    transaction = request.cookies.get(settings.OIDC_TRANSACTION_COOKIE_NAME)
    if not transaction:
        raise HTTPException(status_code=401, detail="OIDC transaction is missing.")
    try:
        claims = await OidcService().authenticate_callback(
            code=code,
            state=state_value,
            transaction_token=transaction,
        )
    except OidcError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    issuer = str(claims["iss"])
    subject = str(claims["sub"])
    email = str(claims["email"]).strip().lower()
    allowed_domains = {
        domain.strip().lower()
        for domain in settings.OIDC_ALLOWED_EMAIL_DOMAINS.split(",")
        if domain.strip()
    }
    if allowed_domains and email.rsplit("@", 1)[-1] not in allowed_domains:
        raise HTTPException(status_code=403, detail="Email domain is not allowed.")

    users = UserRepository(db)
    user = users.get_by_oidc_identity(issuer, subject)
    if (
        user is None
        and settings.OIDC_ALLOW_EMAIL_LINKING
        and claims.get("email_verified") is True
    ):
        user = users.get_by_email(email)
        if user is not None and user.oidc_subject is None:
            user.oidc_issuer = issuer
            user.oidc_subject = subject
            db.commit()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="SSO account is not provisioned or active.",
        )
    membership = OrganizationRepository(db).get_default_membership(user.id)
    if membership is None:
        raise HTTPException(status_code=403, detail="No active organization membership.")

    response = RedirectResponse("/", status_code=303)
    _complete_login(
        user=user,
        membership=membership,
        request=request,
        response=response,
        db=db,
        audit_action="AUTH_LOGIN_OIDC",
    )
    _clear_oidc_cookie(response)
    return response


@router.post("/refresh", response_model=TokenResponse)
def refresh_session(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    raw_token = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Refresh session required.")
    service = AuthSessionService(db)
    try:
        session, replacement = service.rotate(raw_token)
    except RefreshTokenReuseError as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Session has been revoked.") from exc
    except SessionAuthenticationError as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Invalid or expired session.") from exc

    user = UserRepository(db).get_by_id(session.user_id)
    membership = OrganizationRepository(db).get_membership(
        session.user_id,
        session.organization_id,
    )
    organization = OrganizationRepository(db).get(session.organization_id)
    if (
        user is None
        or not user.is_active
        or membership is None
        or membership.id != session.membership_id
        or organization is None
        or not organization.is_active
    ):
        service.repository.revoke(session, "identity_inactive")
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Session identity is inactive.")
    _set_refresh_cookie(response, replacement)
    return _issue_access_token(user, membership, session.id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> None:
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        try:
            payload = decode_access_token(authorization[7:])
            session_id = payload.get("sid")
            session = (
                AuthSessionRepository(db).get(session_id)
                if session_id
                else None
            )
            if session is not None and session.user_id == int(payload["sub"]):
                AuthSessionRepository(db).revoke(session, "logout")
        except (TokenError, TypeError, ValueError, KeyError):
            pass
    raw_token = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if raw_token:
        AuthSessionService(db).revoke_with_token(raw_token)
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
def me(context: CurrentTenant) -> UserResponse:
    return UserResponse.model_validate(context.user).model_copy(
        update={"role": context.role}
    )


@router.get(
    "/organizations",
    response_model=list[OrganizationAccessResponse],
)
def list_organizations(
    context: CurrentTenant,
    db: Session = Depends(get_db),
) -> list[OrganizationAccessResponse]:
    memberships = OrganizationRepository(db).list_active_memberships(
        context.user.id
    )
    return [
        OrganizationAccessResponse(
            organization_id=organization.id,
            name=organization.name,
            slug=organization.slug,
            role=membership.role,
            is_current=organization.id == context.organization_id,
        )
        for organization, membership in memberships
    ]


@router.post(
    "/switch-organization",
    response_model=TokenResponse,
)
def switch_organization(
    request: OrganizationSwitchRequest,
    context: CurrentTenant,
    db: Session = Depends(get_db),
) -> TokenResponse:
    repository = OrganizationRepository(db)
    membership = repository.get_membership(
        context.user.id,
        request.organization_id,
    )
    organization = (
        repository.get(request.organization_id)
        if membership is not None
        else None
    )
    if membership is None or organization is None or not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active organization membership required.",
        )

    if context.session_id is None:
        raise HTTPException(status_code=401, detail="Revocable session required.")
    session = AuthSessionRepository(db).get(context.session_id)
    if session is None or session.user_id != context.user.id:
        raise HTTPException(status_code=401, detail="Session is unavailable.")
    session.organization_id = membership.organization_id
    session.membership_id = membership.id
    session.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return _issue_access_token(context.user, membership, session.id)


@router.get("/sessions", response_model=list[AuthSessionResponse])
def list_sessions(
    context: CurrentTenant,
    db: Session = Depends(get_db),
) -> list[AuthSessionResponse]:
    return [
        AuthSessionResponse(
            id=session.id,
            user_agent=session.user_agent,
            client_ip=session.client_ip,
            created_at=session.created_at,
            last_seen_at=session.last_seen_at,
            expires_at=session.expires_at,
            is_current=session.id == context.session_id,
        )
        for session in AuthSessionRepository(db).list_active_for_user(context.user.id)
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(
    session_id: str,
    context: CurrentTenant,
    response: Response,
    db: Session = Depends(get_db),
) -> None:
    repository = AuthSessionRepository(db)
    session = repository.get(session_id)
    if session is None or session.user_id != context.user.id:
        raise HTTPException(status_code=404, detail="Session not found.")
    repository.revoke(session, "user_revoked")
    if session_id == context.session_id:
        _clear_refresh_cookie(response)
