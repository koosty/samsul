from pydantic import BaseModel, HttpUrl, computed_field
from datetime import timedelta, datetime, timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import jwt, base64
from fastapi import Request, Response, Depends, HTTPException
from typing import Optional
from starlette.status import HTTP_401_UNAUTHORIZED

class Token(BaseModel):
    access_token: str
    refresh_token: str

class OpenidConfiguration(BaseModel):
    issuer: HttpUrl
    response_types_supported: list[str]
    grant_types_supported: list[str]
    scopes_supported: list[str]
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]
    token_endpoint_auth_methods_supported: list[str]
    claims_supported: list[str]
    @computed_field
    @property
    def authorization_endpoint(self) -> str:
        return f'{self.issuer}/login'

    @computed_field
    @property
    def token_endpoint(self) -> str:
        return f'{self.issuer}/token'

    @computed_field
    @property
    def userinfo_endpoint(self) -> str:
        return f'{self.issuer}/userinfo'

    @computed_field
    @property
    def jwks_uri(self) -> str:
        return f'{self.issuer}/jwks'

class Jwk(BaseModel):
    kty: str
    alg: str
    use: str
    kid: str
    n: str
    e: str

def create_token(data: dict, expires_delta: Optional[timedelta] = timedelta(minutes=15))-> Token:
    private_key = load_private_key()
    token_claims = data.copy()
    token_expire = datetime.now(timezone.utc) + expires_delta
    token_claims.update({"exp": token_expire})
    token = jwt.encode(token_claims, private_key, algorithm='RS256')
    return token

def decode_token(token: str) -> dict:
    public_key = load_private_key().public_key()
    try:
        data = jwt.decode(token, public_key, algorithms=['RS256'])
        # if datetime.now(timezone.utc) > data.get("exp"):
        #     raise HTTPException(
        #             status_code=HTTP_401_UNAUTHORIZED,
        #             detail="Token Expired",
        #             headers={"WWW-Authenticate": "Bearer"},
        #         )
        return data
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

_private_key = None
def load_private_key():
    global _private_key
    if _private_key is None:
        with open("private.pem", "rb") as pem_file:
            _private_key = serialization.load_pem_private_key(
                pem_file.read(),
                backend=default_backend(),
                password=None
            )
    return _private_key

def validate_cookie_token(request: Request, response: Response) -> Optional[Token]:
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    if not access_token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return Token(access_token = access_token, refresh_token = refresh_token)

async def get_current_user(token: str = Depends(validate_cookie_token)):
    try:
        user = await oauth.github.parse_id_token(token)
        return user
    except Exception:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
def load_jwks():
    public = load_private_key().public_key()

    public_numbers = public_key.public_numbers()
    e = public_numbers.e
    n = public_numbers.n

    jwk = {
        "kty": "RSA",
        "use": "sig",
        "kid": "default",
        "n": to_base64url_uint(n),
        "e": to_base64url_uint(e),
    }
    return {"keys": [jwk]}

