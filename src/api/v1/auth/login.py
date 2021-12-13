from api.v1.auth.lambda_function import app, logger

import boto3
import json
import os
from time import time
from flask import request
from models.v1.auth import AuthenticationResult, Challenge
from utils.encoders import DataclassEncoder
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import AuthFlows, AuthParameters, ClientMetadata, get_secret_hash
from utils.requests import LOGIN_URL, BodyFields, validate_request_body
from utils.flask import make_exception, make_response, Methods
from typing import Dict
from mypy_boto3_sts.client import STSClient
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
from mypy_boto3_cognito_idp.type_defs import InitiateAuthResponseTypeDef

required_env_vars = [
    EnvironmentVariables.CLIENT_ID,
    EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN,
    EnvironmentVariables.USER_POOL_ID,
]

required_body_fields = [
    BodyFields.USERNAME,
    BodyFields.PASSWORD
]

@app.route(LOGIN_URL, methods=[Methods.POST])
def login():
    env: Dict = os.environ
    validate_environment(env, required_env_vars)

    client_id: str = env[EnvironmentVariables.CLIENT_ID]
    user_pool_id: str = env[EnvironmentVariables.USER_POOL_ID]

    sts_client: STSClient = boto3.Session().client("sts")
    cognito: CognitoIdentityProviderClient = create_sts_session(
        sts_client=sts_client,
        role_arn=env[EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN],
        role_session_name="GET_USER_POOL_INFO",
    ).client("cognito-idp")

    body: Dict = request.json
    try:
        validate_request_body(body, required_body_fields)
    except KeyError as e:
        logger.exception("Invalid Request Body")
        make_exception(400, f"Invalid Request Body: {str(e)}")
    
    username: str = body[BodyFields.USERNAME]
    password: str = body[BodyFields.PASSWORD]

    try:
        secret_hash: str = get_secret_hash(cognito, user_pool_id, username, client_id)

        resp: InitiateAuthResponseTypeDef = cognito.initiate_auth(
            ClientId=client_id,
            AuthFlow=AuthFlows.USER_PASSWORD_AUTH,
            AuthParameters={
                AuthParameters.USERNAME: username,
                AuthParameters.SECRET_HASH: secret_hash,
                AuthParameters.PASSWORD: password,
            },
            ClientMetadata={
                ClientMetadata.USERNAME: username,
                ClientMetadata.PASSWORD: password,
            },
        )
        
        if "AuthenticationResult" in resp:
            result: Dict = resp["AuthenticationResult"]
            body = AuthenticationResult(
                id_token=result["IdToken"],
                refresh_token=result["RefreshToken"],
                access_token=result["AccessToken"],
                expires_in=result["ExpiresIn"],
                token_type=result["TokenType"],
                refresh_after= int(time() + (int(resp["AuthenticationResult"]["ExpiresIn"]) * .9))
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

    except cognito.exceptions.NotAuthorizedException:
        return make_exception(401, "The username or password is incorrect", logger)

    except cognito.exceptions.UserNotConfirmedException:
        return make_exception(403, "User is not confirmed", logger)

    except cognito.exceptions.UserNotFoundException:
        return make_exception(404, "User does not exist", logger)

    except Exception:
        logger.exception("Unknown error: ")
        return make_exception(500, "Server Error. Please try again later", logger)
