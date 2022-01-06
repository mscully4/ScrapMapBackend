from api.v1.auth.lambda_function import app, logger

import boto3
import json
import os
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.cognito import get_secret_hash
from utils.requests import RESPOND_TO_AUTH_CHALLENGE_URL
from flask import request
from utils.flask import make_exception, make_response, Methods

required_env_vars = [
    EnvironmentVariables.CLIENT_ID.name,
    EnvironmentVariables.USER_POOL_ACCESS_ROLE_ARN.name,
    EnvironmentVariables.USER_POOL_ID.name,
]


@app.route(RESPOND_TO_AUTH_CHALLENGE_URL, methods=[Methods.POST])
def respond_to_auth_challenge():
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
    challenge_name = body["challenge_name"]
    challenge_responses = body["challenge_responses"]
    session = body["session"]

    try:
        secret_hash = get_secret_hash(cognito, env, username, client_id)

        challenge_responses["SECRET_HASH"] = secret_hash
        resp = cognito.respond_to_auth_challenge(
            ClientId=client_id,
            ChallengeName=challenge_name,
            Session=session,
            ChallengeResponses=challenge_responses,
        )

    except cognito.exceptions.NotAuthorizedException:
        return make_exception(401, "Invalid Request", logger)
    except cognito.exceptions.UserNotConfirmedException:
        return make_exception(403, "User is not confirmed", logger)
    except Exception:
        return make_exception(500, "Servor Error. please try again later", logger)

    return make_response(200, json.dumps(resp))
