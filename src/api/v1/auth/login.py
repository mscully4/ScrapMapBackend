from api.v1.auth.lambda_function import app, logger

import boto3
import json
import os
from models.v1.auth import AuthenticationResult, Challenge
from utils.encoders import DataclassEncoder
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import AuthFlows, AuthParameters, get_secret_hash
from utils.requests import LOGIN_URL
from flask import request
from utils.flask import make_exception, make_response, Methods


required_env_vars = [
    EnvironmentVariables.CLIENT_ID.name,
    EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name,
    EnvironmentVariables.USER_POOL_ID.name,
]


@app.route(LOGIN_URL, methods=[Methods.POST])
def login():
    env = os.environ

    validate_environment(env, required_env_vars)

    sts_client = boto3.Session().client("sts")
    cognito = create_sts_session(
        sts_client=sts_client,
        role_arn=env[EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name],
        role_session_name="GET_USER_POOL_INFO",
    ).client("cognito-idp")

    client_id = env[EnvironmentVariables.CLIENT_ID.name]

    body = request.json
    username = body["username"]
    password = body["password"]

    try:
        secret_hash = get_secret_hash(cognito, env, username, client_id)

        resp = cognito.initiate_auth(
            ClientId=client_id,
            AuthFlow=AuthFlows.USER_PASSWORD_AUTH,
            AuthParameters={
                AuthParameters.USERNAME: username,
                AuthParameters.SECRET_HASH: secret_hash,
                AuthParameters.PASSWORD: password,
            },
            ClientMetadata={
                "username": username,
                "password": password,
            },
        )

    except cognito.exceptions.NotAuthorizedException:
        return make_exception(401, "The username or password is incorrect", logger)

    except cognito.exceptions.UserNotConfirmedException:
        return make_exception(403, "User is not confirmed", logger)

    except cognito.exceptions.UserNotFoundException:
        return make_exception(404, "User does not exist", logger)

    except Exception:
        return make_exception(500, "Server Error. Please try again later", logger)

    if "AuthenticationResult" in resp:
        result = resp["AuthenticationResult"]
        body = AuthenticationResult(
            id_token=result["IdToken"],
            refresh_token=result["RefreshToken"],
            access_token=result["AccessToken"],
            expires_in=result["ExpiresIn"],
            token_type=result["TokenType"],
        )
        return make_response(200, json.dumps(body, cls=DataclassEncoder))

    if "ChallengeName" in resp:
        body = Challenge(
            challenge_name=resp["ChallengeName"],
            challenge_parameters=resp["ChallengeParameters"],
            session=resp["Session"],
        )
        return make_response(200, json.dumps(body, cls=DataclassEncoder))

    logger.error(
        "Neither AuthenticationResult nor ChallengeName is present in the response"
    )
    return make_exception(500, "Server Error. Please try again later")
