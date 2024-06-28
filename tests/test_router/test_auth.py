from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_read_openid_configuration():
    response = client.get("/auth/.well-known/openid-configuration")
    assert response.status_code == 200
    assert set(response.json().keys()) == {
                'issuer', 
                'authorization_endpoint',
                'token_endpoint', 
                'userinfo_endpoint', 
                'jwks_uri', 
                'response_types_supported', 
                'grant_types_supported', 
                'scopes_supported',
                'claims_supported',
                'id_token_signing_alg_values_supported',
                'subject_types_supported',
                'token_endpoint_auth_methods_supported'
            }
    