from api.v1.auth.lambda_function import app, logger

import boto3
import os
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import get_secret_hash
from utils.requests import RESEND_VERIFICATION_CODE_URL
from flask import request
from utils.flask import make_exception, make_response, Methods

required_env_vars = [
    EnvironmentVariables.CLIENT_ID.name,
    EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name,
    EnvironmentVariables.USER_POOL_ID.name,
]


@app.route(RESEND_VERIFICATION_CODE_URL, methods=[Methods.POST])
def resend_verification_code():
    env = os.environ

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
    username = body["username"]

    try:
        secret_hash = get_secret_hash(username, client_id, client_secret)
        cognito.resend_confirmation_code(
            ClientId=client_id,
            SecretHash=secret_hash,
            Username=username,
        )
        return make_response(204, "")
    except cognito.exceptions.UserNotFoundException:
        return make_exception(404, "User does not exist", logger)
    except cognito.exceptions.InvalidParameterException:
        return make_exception(400, "User is already confirmed", logger)
    except Exception:
        return make_exception(500, "Server Error", logger)
