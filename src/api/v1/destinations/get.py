from typing import Dict
from botocore.exceptions import ClientError
import boto3
import os
import json
from utils.boto3.dynamo import ScrapMapDDBSchema, query_table, DecimalEncoder
from utils.boto3.sts_session import create_sts_session
from utils.boto3.lambda_ import make_response
from utils.environment import EnvironmentVariables, validate_environment
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_sts.client import STSClient
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

required_env_vars = [
    EnvironmentVariables.DYNAMO_READ_ROLE_ARN.name,
    EnvironmentVariables.DYNAMO_TABLE_NAME.name,
]


@event_source(data_class=APIGatewayProxyEvent)
def lambda_handler(event: APIGatewayProxyEvent, context):
    logger.info("Body: %s", event.raw_event)

    logger.info("Validating Environment Variables")
    env: Dict = dict(os.environ)
    validate_environment(env, required_env_vars)

    sts_client: STSClient = boto3.Session().client("sts")
    dynamo: DynamoDBServiceResource = create_sts_session(
        sts_client=sts_client,
        role_arn=env[EnvironmentVariables.DYNAMO_READ_ROLE_ARN.name],
        role_session_name="GET_DESTINATIONS_FOR_USER",
    ).resource("dynamodb")

    table: Table = dynamo.Table(env[EnvironmentVariables.DYNAMO_TABLE_NAME.name])

    # API Gateway will validate that the User parameter exists
    user: str = event.query_string_parameters["user"]

    try:
        logger.info("PK: %s", user)
        response = query_table(table, key=ScrapMapDDBSchema.PK, value=user)
        logger.info("Query Results: %s", response)
        serialized_results = json.dumps(
            response["Items"] if "Items" in response else [], cls=DecimalEncoder
        )
        return make_response(200, serialized_results)
    except ClientError:
        logger.exception("AWS Client Error")
        return make_response(500, "Server Error")
    except Exception:
        logger.exception("An Unknown Error has Occured")
        return make_response(500, "Server Error")
