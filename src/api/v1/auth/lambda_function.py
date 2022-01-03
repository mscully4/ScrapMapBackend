import awsgi
from flask import Flask

import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)


import api.v1.auth.login
import api.v1.auth.create_user
import api.v1.auth.verify_user

def lambda_handler(event, context):
    return awsgi.response(app, event, context)
