import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import secrets


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, _ = stored_hash.split("$", 1)
    except ValueError:
        return False
    computed = hash_password(password, salt)
    return hmac.compare_digest(computed, stored_hash)


def create_access_token(user_id: str, username: str, secret: str, ttl_minutes: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload_json).decode("utf-8").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def decode_access_token(token: str, secret: str) -> dict[str, object] | None:
    try:
        encoded, signature = token.split(".", 1)
    except ValueError:
        return None

    expected = hmac.new(secret.encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None

    padding = "=" * (-len(encoded) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(encoded + padding).decode("utf-8"))
    except Exception:
        return None

    exp = int(payload.get("exp", 0))
    if datetime.now(UTC).timestamp() > exp:
        return None
    return payload


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
