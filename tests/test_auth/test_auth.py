from auth import auth
from datetime import timedelta
from fastapi import HTTPException

def test_create_access_token():
    token = auth.create_token(data={"email":"test@example.com"})
    assert token is not None

def test_decode_token():
    token = auth.create_token(data={"email":"test@example.com"})
    data = auth.decode_token(token) 
    print(data)
    assert data is not None
    assert data['email'] == "test@example.com"

def test_decode_token_expired():
    token = auth.create_token(data={"email":"test@example.com"}, expires_delta=timedelta(days=-1))
    try:
        auth.decode_token(token)
    except Exception as e:
        assert e.status_code == 401
        assert e.detail == "Refresh token expired"
        assert isinstance(e, HTTPException)


    