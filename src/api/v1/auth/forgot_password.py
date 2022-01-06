from api.v1.auth.lambda_function import app, logger

import boto3
import os
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import get_secret_hash
from utils.requests import FORGOT_PASSWORD_URL
from flask import request
from utils.flask import make_exception, make_response, Methods

required_env_vars = [
    EnvironmentVariables.CLIENT_ID.name,
    EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name,
    EnvironmentVariables.USER_POOL_ID.name,
]


@app.route(FORGOT_PASSWORD_URL, methods=[Methods.POST])
def forgot_password():
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

    try:
        secret_hash = get_secret_hash(cognito, env, username, client_id)
        cognito.forgot_password(
            ClientId=client_id,
            SecretHash=secret_hash,
            Username=username,
        )

        return make_response(204, "")

    except cognito.exceptions.UserNotFoundException:
        return make_exception(404, "User doesn't exist", logger)
    except cognito.exceptions.InvalidParameterException:
        return make_exception(400, f"User <{username}> is not confirmed yet", logger)
    except cognito.exceptions.CodeMismatchException:
        return make_exception(400, "Invalid verification code", logger)
    except cognito.exceptions.NotAuthorizedException:
        return make_exception(403, "Not authorized", logger)
    except Exception:
        return make_exception(500, "Server Error. Try again later", logger)
