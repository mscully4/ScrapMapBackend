from typing import Dict
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import QueryOutputTypeDef
from decimal import Decimal
from json import JSONEncoder


class TravelMapTableSchema:
    PK = "PK"
    SK = "SK"
    Entity = "Entity"


class Entities:
    DESTINATION = "DESTINATION"
    PLACE = "PLACE"
    PHOTO = "PHOTO"


class SortKeyFormatStrings:
    DESTINATION = Entities.DESTINATION + "#{place_id}"
    PLACE = Entities.PLACE + "#{place_id}"
    PHOTO = Entities.PHOTO + "#{photo}"


def create_record(pk: str, sk: str, entity: Dict) -> Dict:
    return {
        TravelMapTableSchema.PK: pk,
        TravelMapTableSchema.SK: sk,
        TravelMapTableSchema.Entity: entity,
    }


def query_table(table: Table, key: str = None, value: str = None) -> Dict:
    if key is not None and value is not None:
        filtering_exp = Key(key).eq(value)
        return table.query(KeyConditionExpression=filtering_exp)

    raise ValueError("Parameters missing or invalid")

def query_table_begins_with(table: Table, pk: str, pk_value: str, sk: str, sk_value: str) -> QueryOutputTypeDef:
    filtering_exp = Key(pk).eq(pk_value) & Key(sk).begins_with(sk_value)
    return table.query(KeyConditionExpression=filtering_exp)
