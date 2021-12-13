from api.v1.auth.lambda_function import app, logger

import boto3
import json
import os
from time import time
from flask import request
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import get_secret_hash, AuthFlows, AuthParameters
from utils.requests import REFRESH_TOKENS_URL, BodyFields, validate_request_body
from utils.flask import make_exception, make_response, Methods
from utils.encoders import DataclassEncoder
from models.v1.auth import AuthenticationResult, Challenge
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
    BodyFields.REFRESH_TOKEN
]

@app.route(REFRESH_TOKENS_URL, methods=[Methods.POST])
def refresh_tokens():
    env: Dict = dict(os.environ)
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
    refresh_token: str = body[BodyFields.REFRESH_TOKEN]

    try:
        secret_hash: str = get_secret_hash(cognito, user_pool_id, username, client_id)

        resp: InitiateAuthResponseTypeDef = cognito.initiate_auth(
            ClientId=client_id,
            AuthFlow=AuthFlows.REFRESH_TOKEN_AUTH,
            AuthParameters={
                AuthParameters.REFRESH_TOKEN: refresh_token,
                AuthParameters.SECRET_HASH: secret_hash,
            },
        )
        
        if "AuthenticationResult" in resp:
            result: Dict = resp["AuthenticationResult"]
            body: AuthenticationResult = AuthenticationResult(
                id_token=result["IdToken"],
                refresh_token=refresh_token,
                access_token=result["AccessToken"],
                expires_in=result["ExpiresIn"],
                token_type=result["TokenType"],
                refresh_after= int(time() + (int(resp["AuthenticationResult"]["ExpiresIn"]) * .9))
            )
            return make_response(200, json.dumps(body, cls=DataclassEncoder))

        
        if "ChallengeName" in resp:
            body: Challenge = Challenge(
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
        return make_exception(401, "Invalid Token", logger)

    except cognito.exceptions.InvalidParameterException:
        return make_exception(400, "Invalid Parameter", logger)

    except Exception:
        logger.exception("Unknown error: ")
        return make_exception(500, "Server Error. Please try again later", logger)
