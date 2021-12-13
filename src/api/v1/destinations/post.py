import boto3
import os
import logging
from botocore.exceptions import ClientError
from utils.boto3.dynamo import SortKeyFormatStrings, create_record
from utils.boto3.sts_session import create_sts_session
from utils.environment import EnvironmentVariables, validate_environment
from utils.boto3.lambda_function import make_response
from models.v1.destination import Destination
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)
from mypy_boto3_sts.client import STSClient
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_dynamodb.type_defs import PutItemOutputTypeDef
from typing import Dict

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

required_env_vars = [
    EnvironmentVariables.DYNAMO_WRITE_ROLE_ARN,
    EnvironmentVariables.DYNAMO_TABLE_NAME,
]


@event_source(data_class=APIGatewayProxyEvent)
def lambda_handler(event: APIGatewayProxyEvent, context):
    logger.info("Event: %s", event.raw_event)

    logger.info("Validating Environment Variables")
    env: Dict = os.environ
    validate_environment(env, required_env_vars)

    logger.info("Generating Dynamo Resource with Assumed Role")
    sts_client: STSClient = boto3.Session().client("sts")
    dynamo: DynamoDBServiceResource = create_sts_session(
        sts_client=sts_client,
        role_arn=env[EnvironmentVariables.DYNAMO_WRITE_ROLE_ARN],
        role_session_name="CREATE_NEW_DESTINATION",
    ).resource("dynamodb")

    table: Table = dynamo.Table(env[EnvironmentVariables.DYNAMO_TABLE_NAME])

    try:
        logger.info("Body: %s", event.raw_event)

        destination: Destination = Destination(**event.json_body)

        username: str = event.request_context.authorizer.claims.get("cognito:username")
        sk: str = SortKeyFormatStrings.DESTINATION.format(place_id=destination.place_id)

        item: dict = create_record(username, sk, destination.asdict())
        logger.info("Item: %s", item)

        response: PutItemOutputTypeDef = table.put_item(Item=item)
        logger.info("Response: %s", response)
        return make_response(204, "")
    except TypeError:
        logger.exception("Invalid Request Body")
        make_response(400, "Invalid Request Body")
    except ClientError:
        logger.exception("AWS Client Error")
        return make_response(500, "Server Error")
    except Exception:
        logger.exception("An Unknown Error Has Occured")
        return make_response(500, "Internal Server Error")
