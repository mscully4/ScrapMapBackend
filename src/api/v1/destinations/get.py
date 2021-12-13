import boto3
import os
import json
import logging
from botocore.exceptions import ClientError
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)
from utils.requests import BodyFields
from utils.encoders import DecimalEncoder
from utils.boto3.dynamo import TravelMapTableSchema, query_table_begins_with, Entities
from utils.boto3.sts_session import create_sts_session
from utils.boto3.lambda_function import make_response
from utils.environment import EnvironmentVariables, validate_environment
from mypy_boto3_sts.client import STSClient
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_dynamodb.type_defs import QueryOutputTypeDef
from typing import Dict

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

required_env_vars = [
    EnvironmentVariables.DYNAMO_READ_ROLE_ARN,
    EnvironmentVariables.DYNAMO_TABLE_NAME,
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
        role_arn=env[EnvironmentVariables.DYNAMO_READ_ROLE_ARN],
        role_session_name="GET_DESTINATIONS_FOR_USER",
    ).resource("dynamodb")

    table: Table = dynamo.Table(env[EnvironmentVariables.DYNAMO_TABLE_NAME])

    # API Gateway will validate that the User parameter exists
    user: str = event.query_string_parameters[BodyFields.USER]

    try:
        logger.info("PK: %s", user)
        response: QueryOutputTypeDef = query_table_begins_with(
            table, pk=TravelMapTableSchema.PK, pk_value=user, sk=TravelMapTableSchema.SK, sk_value=Entities.DESTINATION
        )
        logger.info("Query Results: %s", response)
        serialized_results: str = json.dumps(
            response["Items"] if "Items" in response else [], cls=DecimalEncoder
        )
        return make_response(200, serialized_results)
    except ClientError:
        logger.exception("AWS Client Error")
        return make_response(500, "Server Error")
    except Exception:
        logger.exception("An Unknown Error has Occured")
        return make_response(500, "Server Error")
