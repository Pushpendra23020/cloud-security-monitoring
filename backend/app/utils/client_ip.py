from ipaddress import ip_address, ip_network

from fastapi import Request

from app.config import settings


def resolve_client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    try:
        peer_address = ip_address(peer)
    except ValueError:
        return peer

    trusted_networks = []
    for value in settings.AUTH_TRUSTED_PROXY_CIDRS.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            trusted_networks.append(ip_network(value, strict=False))
        except ValueError:
            continue
    if not any(peer_address in network for network in trusted_networks):
        return peer

    forwarded = request.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
    try:
        return str(ip_address(forwarded)) if forwarded else peer
    except ValueError:
        return peer
