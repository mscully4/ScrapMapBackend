from enum import Enum, auto
from typing import Dict, List


class EnvironmentVariables(Enum):
    USER_POOL_ID = auto()
    CLIENT_ID = auto()
    USER_POOL_ACCESS_ROLE_ARN = auto()
    DYNAMO_TABLE_NAME = auto()
    DYNAMO_READ_ROLE_ARN = auto()
    DYNAMO_WRITE_ROLE_ARN = auto()


def validate_environment(env: Dict, required_env_vars: List):
    for env_var in required_env_vars:
        if env_var not in env:
            raise KeyError(f"Environment varibale {env_var} does not exist")
