from fastapi import APIRouter, Request, Response, Cookie, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, Union
from auth.auth import OpenidConfiguration, create_token
from authlib.oauth2.rfc6749 import grants
from authlib.integrations.httpx_client import AsyncOAuth2Client
from starlette.config import Config
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from config.config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI, GITHUB_ACCESS_TOKEN_URL, GITHUB_AUTHORIZATION_URL, GITHUB_USER_INFO_URL
from datetime import timedelta, timezone, datetime

# OAuth2 setup
oauth2_client = AsyncOAuth2Client(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    redirect_uri=GITHUB_REDIRECT_URI
)

router = APIRouter(prefix= '/auth')

@router.get("/.well-known/openid-configuration")
async def openid_configuration():
    return OpenidConfiguration(
            issuer = 'https://accounts.google.com',
            response_types_supported = ['code'],
            grant_types_supported = ['authorization_code'],
            scopes_supported = ['openid', 'email', 'profile'],
            subject_types_supported = ['public'],
            id_token_signing_alg_values_supported = ['RS256'],
            token_endpoint_auth_methods_supported = ['client_secret_post'],
            claims_supported = ['aud', 'email', 'exp', 'iat', 'iss', 'sub']
        )

@router.get("/login")
async def login(request: Request):
    authorization_url, state_token = oauth2_client.create_authorization_url(GITHUB_AUTHORIZATION_URL)
    print(authorization_url)
    response = RedirectResponse(authorization_url)
    response.set_cookie(key="state_token", value=state_token, httponly=True, samesite='Lax')
    return response

@router.get("/callback")
async def auth_callback(code: str, state: str, state_token: Annotated[Union[str, None], Cookie()] = None):
    print(f"code: {code}, state: {state}, state_token_cookie: {state_token}")
    if not state or state != state_token:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid state")

    token = await oauth2_client.fetch_token(GITHUB_ACCESS_TOKEN_URL, code=code)
    response = await oauth2_client.get(GITHUB_USER_INFO_URL, headers={
            'Authorization': f'Bearer {token["access_token"]}'
        })
    if response.status_code != 200:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=response.text)

    refresh_token = create_token(data={"email": response.json()["email"]}, expires_delta=timedelta(days=7))
    redirect = RedirectResponse(url='/')
    redirect.delete_cookie(key="state_token")
    redirect.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite='Lax', expires=datetime.now(timezone.utc) + timedelta(days=7))
    return redirect

@router.post("/refresh-token")
async def refresh_token(response: Response, refresh_token: Annotated[Union[str, None], Cookie()] = None):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("scope") != "refresh_token":
            raise HTTPException(status_code=401, detail="Invalid scope for token")
        
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        
        response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="Lax")
        return {"access_token": access_token, "token_type": "bearer"}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")