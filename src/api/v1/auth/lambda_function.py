import awsgi
from flask import Flask

import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)


def lambda_handler(event, context):
    return awsgi.response(app, event, context)
