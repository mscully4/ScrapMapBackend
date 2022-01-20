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


class AuthBodyFields:
    USERNAME = "username"
    REFRESH_TOKEN = "refresh_token"
