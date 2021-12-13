from typing import Dict, List

from models.v1.destination import Destination

V1_BASE_URL = ""
AUTH_URL = V1_BASE_URL + "/auth"

LOGIN_URL = f"{AUTH_URL}/login"
CREATE_USER_URL = f"{AUTH_URL}/create_user"
VERIFY_USER_URL = f"{AUTH_URL}/verify_user"
REFRESH_TOKENS_URL = f"{AUTH_URL}/refresh_tokens"
FORGOT_PASSWORD_URL = f"{AUTH_URL}/forgot_password"
CONFIRM_FORGOT_PASSWORD_URL = f"{AUTH_URL}/confim_forgot_password"
CHANGE_PASSWORD_URL = f"{AUTH_URL}/change_password"
RESPOND_TO_AUTH_CHALLENGE_URL = f"{AUTH_URL}/respond_to_auth_challenge"
RESEND_VERIFICATION_CODE_URL = f"{AUTH_URL}/resend_verification_code"

def validate_request_body(body: Dict, required_body_fields: List):
    for field in required_body_fields:
        if field not in body:
            raise KeyError(f"Field {field} is required")


class BodyFields:
    USERNAME = "username"
    PASSWORD = "password"
    EMAIL = "email"
    REFRESH_TOKEN = "refresh_token"
    CONFIRMATION_CODE = "confirmation_code"
    USER = "user"

class QueryStringParameters:
    DESTINATION_ID = "destination_id"
    PLACE_ID = "place_id"
