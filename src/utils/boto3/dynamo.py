from typing import Dict
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table
from decimal import Decimal
from json import JSONEncoder


class ScrapMapDDBSchema:
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


def create_record(pk: str, sk: str, entity) -> Dict:
    return {
        ScrapMapDDBSchema.PK: pk,
        ScrapMapDDBSchema.SK: sk,
        ScrapMapDDBSchema.Entity: entity,
    }


def query_table(table: Table, key: str = None, value: str = None) -> Dict:
    if key is not None and value is not None:
        filtering_exp = Key(key).eq(value)
        return table.query(KeyConditionExpression=filtering_exp)

    raise ValueError("Parameters missing or invalid")


class DecimalEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)
