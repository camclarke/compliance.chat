import jwt
from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWKClient

security = HTTPBearer()

# Entra External ID CIAM Tenant Details
CLIENT_ID = "b2d79546-175d-4a3e-9e0a-466bd6d291b6"
TENANT_ID = "46f1d642-3c77-472b-8482-58028085c788"

# The discovery endpoint for the JWKS keys provided by Microsoft Entra ID
JWKS_URL = f"https://compliancechat.ciamlogin.com/{TENANT_ID}/discovery/v2.0/keys"
jwks_client = PyJWKClient(JWKS_URL)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Validates the Bearer token sent in the Authorization header against
    Microsoft Entra External ID's public signing keys.
    """
    token = credentials.credentials
    try:
        # Fetch the signing key from the JWKS matching the token's kid header
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Verify and decode the token
        payload = jwt.decode(
            token,
            key=signing_key.key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=f"https://compliancechat.ciamlogin.com/{TENANT_ID}/v2.0"
        )
        return payload

    except jwt.exceptions.PyJWKClientError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unable to fetch signing key from Entra ID: {str(error)}"
        )
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature has expired."
        )
    except jwt.exceptions.InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(error)}"
        )
