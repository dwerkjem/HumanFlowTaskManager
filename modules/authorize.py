import requests
import os

from jose import jwt
from jose.exceptions import JWTError
from flask import session, redirect
from authlib.integrations.flask_client import OAuth


def authorize(oauth):
    token_response = oauth.google.authorize_access_token()
    id_token = token_response.get('id_token')
    if not id_token:
        return "ID token not found in the response.", 400

    try:
        # Fetch Google's public keys
        jwks_url = "https://www.googleapis.com/oauth2/v3/certs"
        jwks = requests.get(jwks_url).json()

        # Get key ID from token header
        header = jwt.get_unverified_header(id_token)
        kid = header['kid']

        # Find the matching public key
        key = None
        for jwk in jwks['keys']:
            if jwk['kid'] == kid:
                key = jwk
                break

        if not key:
            return "Matching public key not found", 400

        # Construct the public key
        from jose import jwk
        from jose.utils import base64url_decode

        public_key = jwk.construct(key)
        message, encoded_signature = id_token.rsplit('.', 1)
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))

        # Verify the signature
        if not public_key.verify(message.encode("utf-8"), decoded_signature):
            return "Signature verification failed.", 400

        # Decode and verify the ID token
        decoded_token = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=os.getenv("GOOGLE_CLIENT_ID"),
            issuer="https://accounts.google.com",
            options={"verify_at_hash": False} # Disable hash verification for now
        )

        # Store user information
        session["user"] = {
            "name": decoded_token.get("name"),
            "email": decoded_token.get("email"),
            "picture": decoded_token.get("picture"),
        }

        return redirect("/")

    except (JWTError, StopIteration) as e:
        return f"Token verification failed: {str(e)}", 400