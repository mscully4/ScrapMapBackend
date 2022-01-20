import boto3
import os
from utils.boto3.dynamo import SortKeyFormatStrings, create_record
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.lambda_ import make_response
from models.v1 import Place
from botocore.exceptions import ClientError
import logging
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

required_env_vars = [
    EnvironmentVariables.DYNAMO_WRITE_ROLE_ARN.name,
    EnvironmentVariables.DYNAMO_TABLE_NAME.name,
]


@event_source(data_class=APIGatewayProxyEvent)
def lambda_handler(event: APIGatewayProxyEvent, context):
    logger.info("Event: %s", event.raw_event)

    logger.info("Validating Environment Variables")
    env = os.environ
    validate_environment(env, required_env_vars)

    logger.info("Generating Dynamo Resource with Assumed Role")
    sts_client = boto3.Session().client("sts")
    dynamo = create_sts_session(
        sts_client=sts_client,
        role_arn=env[EnvironmentVariables.DYNAMO_WRITE_ROLE_ARN.name],
        role_session_name="CREATE_NEW_PLACE",
    ).resource("dynamodb")

    table = dynamo.Table(env[EnvironmentVariables.DYNAMO_TABLE_NAME.name])

    try:
        logger.info("Body: %s", event.raw_event)
        place: Place = Place(**event.json_body)

        username: str = event.request_context.authorizer.claims.get("cognito:username")
        sk = SortKeyFormatStrings.PLACE.format(place_id=place.place_id)

        item = create_record(username, sk, place.asdict())
        logger.info("Item: %s", item)

        response = table.put_item(Item=item)
        logger.info("Response: %s", response)
        return make_response(204, "")
    except ClientError:
        logger.exception("AWS Client Error")
        return make_response(500, "Server Error")
    except Exception:
        logger.exception("An Unknown Error Has Occured")
        return make_response(500, "Internal Server Error")
