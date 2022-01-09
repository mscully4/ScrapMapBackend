from api.v1.auth.lambda_function import app, logger

import boto3
import os
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.requests import CHANGE_PASSWORD_URL
from flask import request
from utils.flask import make_exception, make_response, Methods


required_env_vars = [
    EnvironmentVariables.CLIENT_ID.name,
    EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name,
    EnvironmentVariables.USER_POOL_ID.name,
]


@app.route(CHANGE_PASSWORD_URL, methods=[Methods.POST])
def change_password():
    env = os.environ

    validate_environment(env, required_env_vars)

    sts_client = boto3.Session().client("sts")
    cognito = create_sts_session(
        sts_client=sts_client,
        role_arn=env[EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name],
        role_session_name="GET_USER_POOL_INFO",
    ).client("cognito-idp")

    body = request.json

    access_token = body["access_token"]
    previous_password = body["previous_password"]
    proposed_password = body["proposed_password"]

    try:
        cognito.change_password(
            AccessToken=access_token,
            PreviousPassword=previous_password,
            ProposedPassword=proposed_password,
        )

        return make_response(204, "")

    except Exception:
        make_exception(500, "Server Error", logger)
