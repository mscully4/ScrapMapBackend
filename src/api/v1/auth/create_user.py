from api.v1.auth.lambda_function import app, logger

import boto3
import os
from flask import request, Response
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import get_secret_hash
from utils.requests import BodyFields, validate_request_body
from utils.requests import CREATE_USER_URL
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
    BodyFields.USERNAME,
    BodyFields.PASSWORD,
    BodyFields.EMAIL
]

@app.route(CREATE_USER_URL, methods=[Methods.POST])
def create_user() -> Response:
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
    email: str = body[BodyFields.EMAIL]

    try:
        secret_hash: str = get_secret_hash(cognito, user_pool_id, username, client_id)

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
