"""
Module provides utilities around boto3 sessions (e.g. creating boto3 sessions
with custom providers).
"""
from typing import Any, Dict, List, Optional

import boto3.session
import botocore.credentials
import botocore.session
from mypy_boto3.boto3_session import Session
from mypy_boto3_sts import STSClient
from mypy_boto3_sts.type_defs import AssumeRoleRequestRequestTypeDef


class _StsCredentialProvider(botocore.credentials.CredentialProvider):
    """
    Implements the `CredentialProvider` by assuming a role with the parameters
    provided in the constructor.

    This will fail early during the first `load` attempt instead of hiding/logging
    the failure as is done in `botocore_sts_credential_provider`.  We want to fail
    as soon as we try to assume a role instead of failing when trying to invoke a
    client method on a session with no credentials.
    """

    def __init__(
        self,
        *,
        sts_client: STSClient,
        role_arn: str,
        role_session_name: str,
        role_external_id: Optional[str] = None
    ):
        self._sts_client = sts_client
        self._role_arn = role_arn
        self._role_session_name = role_session_name
        self._role_external_id = role_external_id

        super().__init__()

    def _fetcher(self):
        assume_role_kwargs = AssumeRoleRequestRequestTypeDef(
            RoleArn=self._role_arn,
            RoleSessionName=self._role_session_name,
        )
        if self._role_external_id:
            assume_role_kwargs["ExternalId"] = self._role_external_id

        response = self._sts_client.assume_role(**assume_role_kwargs)
        credentials = response["Credentials"]

        return {
            "access_key": credentials["AccessKeyId"],
            "secret_key": credentials["SecretAccessKey"],
            "token": credentials["SessionToken"],
            "expiry_time": credentials["Expiration"].isoformat(),
        }

    def load(self):
        metadata = self._fetcher()

        return botocore.credentials.RefreshableCredentials.create_from_metadata(
            metadata=metadata, refresh_using=self._fetcher, method="sts"
        )


def _create_custom_session(
    credential_providers: List[botocore.credentials.CredentialProvider],
    boto3_session_kwargs: Optional[Dict[str, Any]] = None,
) -> Session:
    botocore_session = botocore.session.Session()
    botocore_session.get_component(
        "credential_provider"
    ).providers = credential_providers

    new_session_kwargs = boto3_session_kwargs if boto3_session_kwargs else {}
    session = boto3.session.Session(
        **new_session_kwargs, botocore_session=botocore_session
    )
    return session


def create_sts_session(
    *,
    sts_client: STSClient,
    role_arn: str,
    role_session_name: str,
    role_external_id: Optional[str] = None,
    boto3_session_kwargs: Optional[Dict[str, Any]] = None
) -> Session:
    provider = _StsCredentialProvider(
        sts_client=sts_client,
        role_arn=role_arn,
        role_session_name=role_session_name,
        role_external_id=role_external_id,
    )
    return _create_custom_session([provider], boto3_session_kwargs=boto3_session_kwargs)
