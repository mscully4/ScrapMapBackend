import boto3
import os
import logging
from botocore.exceptions import ClientError
from utils.requests import QueryStringParameters
from utils.boto3.dynamo import SortKeyFormatStrings, TravelMapTableSchema
from utils.boto3.sts_session import create_sts_session
from utils.boto3.lambda_function import make_response
from utils.environment import EnvironmentVariables, validate_environment
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_sts.client import STSClient
from mypy_boto3_dynamodb.type_defs import DeleteItemOutputTypeDef
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
    env: Dict = dict(os.environ)
    validate_environment(env, required_env_vars)

    sts_client: STSClient = boto3.Session().client("sts")
    dynamo: DynamoDBServiceResource = create_sts_session(
        sts_client=sts_client,
        role_arn=env[EnvironmentVariables.DYNAMO_WRITE_ROLE_ARN],
        role_session_name="DELETE_PLACE",
    ).resource("dynamodb")

    table: Table = dynamo.Table(env[EnvironmentVariables.DYNAMO_TABLE_NAME])

    username: str = event.request_context.authorizer.claims.get("cognito:username")

    # API Gateway will validate that the place_id parameter exists
    place_id: str = event.query_string_parameters[QueryStringParameters.PLACE_ID]
    sk: str = SortKeyFormatStrings.PLACE.format(place_id=place_id)
    logger.info("PK: %s", username)
    logger.info("SK: %s", sk)
    
    try:
        response: DeleteItemOutputTypeDef = table.delete_item(
            Key={
                TravelMapTableSchema.PK: username,
                TravelMapTableSchema.SK: sk
            }
        )
        logger.info("Result: %s", response)
        return make_response(204, "")
    except ClientError:
        logger.exception("AWS Client Error")
        return make_response(500, "Server Error")
    except Exception:
        logger.exception("An Unknown Error has Occured")
        return make_response(500, "Server Error")
