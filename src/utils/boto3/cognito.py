import hmac
import hashlib as hl
import base64
from typing import Dict
from mypy_boto3_cognito_idp.client import CognitoIdentityProviderClient
from utils.environment import EnvironmentVariables


class AuthFlows:
    REFRESH_TOKEN_AUTH = "REFRESH_TOKEN_AUTH"
    USER_PASSWORD_AUTH = "USER_PASSWORD_AUTH"


class AuthParameters:
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"
    REFRESH_TOKEN = "REFRESH_TOKEN"
    SECRET_HASH = "SECRET_HASH"


class ClientMetadata:
    USERNAME = "username"
    PASSWORD = "password"


def _calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    msg = username + client_id
    dig = hmac.new(
        str(client_secret).encode("utf-8"),
        msg=str(msg).encode("utf-8"),
        digestmod=hl.sha256,
    ).digest()
    d2 = base64.b64encode(dig).decode()
    return d2


def get_secret_hash(
    cognito: CognitoIdentityProviderClient, user_pool_id: str, username: str, client_id: str
) -> str:
    client_secret = get_client_secret(cognito, user_pool_id, client_id)
    return _calculate_secret_hash(username, client_id, client_secret)


def get_client_secret(
    cognito: CognitoIdentityProviderClient, user_pool_id: str, client_id: str
) -> str:

    response = cognito.describe_user_pool_client(
        UserPoolId=user_pool_id, ClientId=client_id
    )

    return response["UserPoolClient"]["ClientSecret"]
