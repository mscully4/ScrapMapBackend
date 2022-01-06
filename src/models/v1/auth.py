from dataclasses import dataclass


@dataclass
class AuthenticationResult:
    id_token: str
    refresh_token: str
    access_token: str
    expires_in: str
    token_type: str


@dataclass
class Challenge:
    challenge_name: str
    challenge_parameters: str
    session: str
