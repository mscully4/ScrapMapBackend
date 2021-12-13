from api.v1.auth.lambda_function import app, logger

import boto3
import os
from flask import request
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import get_secret_hash
from utils.requests import RESEND_VERIFICATION_CODE_URL, BodyFields, validate_request_body
from utils.flask import make_exception, make_response, Methods
from typing import Dict
from mypy_boto3_sts.client import STSClient
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient

required_env_vars = [
    EnvironmentVariables.CLIENT_ID,
    EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN,
    EnvironmentVariables.USER_POOL_ID,
]

required_body_fields = [
    BodyFields.USERNAME
]


@app.route(RESEND_VERIFICATION_CODE_URL, methods=[Methods.POST])
def resend_verification_code():
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

    try:
        secret_hash: str = get_secret_hash(cognito, user_pool_id, username, client_id)
        cognito.resend_confirmation_code(
            ClientId=client_id,
            SecretHash=secret_hash,
            Username=username,
        )
        return make_response(204, "")
    except cognito.exceptions.InvalidParameterException:
        return make_exception(400, "User is already confirmed", logger)
    except cognito.exceptions.UserNotFoundException:
        return make_exception(404, "User does not exist", logger)
    except Exception:
        logger.exception("Unknown error: ")
        return make_exception(500, "Server Error", logger)
