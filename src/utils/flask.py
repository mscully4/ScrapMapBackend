import json
from flask import Response
from logging import Logger


class Methods:
    GET = "GET"
    POST = "POST"


def make_response(status: int, body: str) -> Response:
    return Response(body, status=status, mimetype="application/json")


def make_exception(status: int, msg: str, logger: Logger = None) -> Response:
    if logger:
        logger.exception(msg)
    return Response(
        json.dumps({"message": msg}), status=status, mimetype="application/json"
    )
