from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

SECRET_KEY = "simdaa_secret_key"
ALGORITHM = "HS256"

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials.strip()

    # Accept both:
    # token
    # Bearer token
    if token.lower().startswith("bearer "):
        token = token[7:]

    print("TOKEN =", token)

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        print("PAYLOAD =", payload)
        return payload

    except JWTError as e:
        print("JWT ERROR =", str(e))
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
