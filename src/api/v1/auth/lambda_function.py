import awsgi
from flask import Flask

import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)


import api.v1.auth.login

def lambda_handler(event, context):
    return awsgi.response(app, event, context)
