from api.v1.auth.lambda_function import app, logger

import boto3
import json
import os
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import get_secret_hash, AuthFlows, AuthParameters
from utils.requests import REFRESH_TOKENS_URL, AuthBodyFields
from flask import request
from utils.flask import make_exception, make_response, Methods


required_env_vars = [
    EnvironmentVariables.CLIENT_ID.name,
    EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name,
    EnvironmentVariables.USER_POOL_ID.name,
]


@app.route(REFRESH_TOKENS_URL, methods=[Methods.POST])
def refresh_tokens():
    env = dict(os.environ)

    validate_environment(env, required_env_vars)

    sts_client = boto3.Session().client("sts")
    cognito = create_sts_session(
        sts_client=sts_client,
        role_arn=env[EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name],
        role_session_name="GET_USER_POOL_INFO",
    ).client("cognito-idp")

    client_id = env[EnvironmentVariables.CLIENT_ID.name]
    user_pool_id = env[EnvironmentVariables.USER_POOL_ID.name]

    response = cognito.describe_user_pool_client(
        UserPoolId=user_pool_id, ClientId=client_id
    )

    client_secret = response["UserPoolClient"]["ClientSecret"]

    body = request.json
    username = body[AuthBodyFields.USERNAME]
    refresh_token = body[AuthBodyFields.REFRESH_TOKEN]

    secret_hash = get_secret_hash(username, client_id, client_secret)

    try:
        client = boto3.client("cognito-idp")

        secret_hash = get_secret_hash(username, client_id, client_secret)
        resp = client.initiate_auth(
            ClientId=client_id,
            AuthFlow=AuthFlows.REFRESH_TOKEN_AUTH,
            AuthParameters={
                AuthParameters.REFRESH_TOKEN: refresh_token,
                AuthParameters.SECRET_HASH: secret_hash,
            },
        )

        body = {}
        if "AuthenticationResult" in resp:
            body["IdToken"] = resp["AuthenticationResult"]["IdToken"]
            body["AccessToken"] = resp["AuthenticationResult"]["AccessToken"]
            body["ExpiresIn"] = resp["AuthenticationResult"]["ExpiresIn"]
            body["TokenType"] = resp["AuthenticationResult"]["TokenType"]
        elif "ChallengeName" in resp:
            body["ChallengeName"] = resp["ChallengeName"]
            body["ChallengeParameters"] = resp["ChallengeParameters"]
            body["Session"] = resp["Session"]

        if not body:
            return make_exception(500, "Server Error", logger)

        return make_response(200, json.dumps(body))

    except Exception as e:
        return make_exception(500, str(e), logger)
