from typing import Dict


def make_response(status_code: int, body: str, headers: Dict = None):
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": body,
    }
