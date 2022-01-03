from api.v1.auth.lambda_function import app, logger

import boto3
import os
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import get_secret_hash
from utils.requests import CREATE_USER_URL
from flask import request, Response
from utils.flask import make_exception, make_response, Methods

required_env_vars = [
    EnvironmentVariables.CLIENT_ID.name,
    EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name,
    EnvironmentVariables.USER_POOL_ID.name,
]


@app.route(CREATE_USER_URL, methods=[Methods.POST])
def create_user() -> Response:
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
    email = body["email"]

    try:
        secret_hash = get_secret_hash(cognito, env, username, client_id)

        cognito.sign_up(
            ClientId=client_id,
            SecretHash=secret_hash,
            Username=username,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
            ValidationData=[{"Name": "email", "Value": email}],
        )
        return make_response(status=204, body="")

    except cognito.exceptions.UsernameExistsException:
        return make_exception(
            400, "An account with this username already exists", logger
        )

    except cognito.exceptions.InvalidPasswordException:
        return make_exception(
            400,
            "Invalid password. Password should have at least one uppercase letter, \
            one lowercase letter and one number",
            logger,
        )

    except cognito.exceptions.UserLambdaValidationException:
        return make_exception(400, "An account with this email already exists", logger)

    except Exception:
        return make_exception(500, "Error. Please try again later", logger)
