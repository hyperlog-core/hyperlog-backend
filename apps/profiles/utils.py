import json
import logging

import boto3
import botocore
import requests

from django.conf import settings
from django.shortcuts import render
from django.utils import timezone

from apps.base.utils import (
    create_model_object,
    get_aws_client,
    get_or_create_sns_topic_by_topic_name,
)

DDB_PROFILES_TABLE = settings.AWS_DDB_PROFILES_TABLE
DDB_PROFILE_ANALYSIS_TABLE = settings.AWS_DDB_PROFILE_ANALYSIS_TABLE
DDB_REPO_ANALYSIS_TABLE = settings.AWS_DDB_REPO_ANALYSIS_TABLE
SNS_PROFILE_ANALYSIS_TOPIC = settings.AWS_SNS_PROFILE_ANALYSIS_TOPIC

LAMBDA_INITIAL_ANALYSIS_FUNCTION = (
    settings.AWS_LAMBDA_INITIAL_ANALYSIS_FUNCTION
)
LAMBDA_INVOCATION_SOURCE = settings.AWS_LAMBDA_INVOCATION_SOURCE

GITHUB_SUCCESS_TEMPLATE_PATH = "profiles/github_success.html"
GITHUB_FAIL_TEMPLATE_PATH = "profiles/github_fail.html"

STACK_OVERFLOW_API_BASE_URL = "https://api.stackexchange.com/2.2"
STACK_OVERFLOW_KEY = settings.STACK_OVERFLOW_KEY


logger = logging.getLogger(__name__)


def render_github_oauth_success(request, **kwargs):
    """
    Example call:
    ```python
        # From inside a view function
        return render_github_oauth_success(request)
    ```
    """
    return render(request, GITHUB_SUCCESS_TEMPLATE_PATH, kwargs)


def render_github_oauth_fail(request, **kwargs):
    """
    Example call:
    ```python
        # From inside a view function
        return render_github_oauth_fail(
            request, errors=["error1", "error2"],
        )
    ```
    """
    return render(request, GITHUB_FAIL_TEMPLATE_PATH, kwargs)


def dynamodb_create_or_update_profile(profile):
    """Uses DynamoDB UpdateItem to create/update a profile on DynamoDB"""
    client = get_aws_client("dynamodb")

    key = {"user_id": {"S": str(profile.user.id)}}
    expression_attribute_names = {"#AT": "%s_access_token" % profile.provider}
    expression_attribute_values = {":t": {"S": profile.access_token}}
    update_expression = "SET #AT = :t"

    return client.update_item(
        TableName=DDB_PROFILES_TABLE,
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
    )


def dynamodb_get_profile(user_id):
    """
    Uses the DynamoDB GetItem API to get the profile data as per the "profiles"
    table in high level python compatible format
    """
    ddb = boto3.resource("dynamodb")

    table = ddb.Table(DDB_PROFILES_TABLE)
    response = table.get_item(Key={"user_id": str(user_id)})
    return response["Item"]


def publish_profile_analysis_trigger_to_sns(user_id, github_token):
    """
    Publish required details for profile analysis task (user_id, github_token)
    to the SNS Topic for profile analysis
    """
    topic = get_or_create_sns_topic_by_topic_name(SNS_PROFILE_ANALYSIS_TOPIC)
    return topic.publish(
        Message=str(timezone.now().timestamp()),
        MessageAttributes={
            "user_id": {"DataType": "String", "StringValue": str(user_id)},
            "github_token": {
                "DataType": "String",
                "StringValue": github_token,
            },
        },
    )


def create_profile_object(profile_model, **kwargs):
    """
    Creates profile with create_model_object and uploads the token to dynamodb
    """
    profile_creation = create_model_object(profile_model, **kwargs)

    if profile_creation.success:
        try:
            invoke_initial_analysis_lambda(profile_creation.object)
        except botocore.exceptions.ClientError:
            logger.error(
                "Lambda initial analysis exception encountered", exc_info=True
            )

    return profile_creation


def dynamodb_add_selected_repos_to_profile_analysis_table(
    user_id, repos_list, max_repos=5
):
    """
    Updates the profile analysis table with selectedRepos field of type String
    Set ({"SS": ["repo1.nameWithOwner", "repo2.nameWithOwner", ...]})

    Uses DynamoDB UpdateItem API
    """
    # input checks
    assert all(
        [isinstance(repo_name, str) for repo_name in repos_list]
    ), "Invalid input"
    assert len(repos_list) > 0 and len(repos_list) <= max_repos, (
        "You must choose at least 1 and at most %i repos" % max_repos
    )

    # Add repos list as String Set
    client = get_aws_client("dynamodb")
    key = {"uuid": {"S": str(user_id)}}
    update_expression = "SET selectedRepos = :reposSet"
    expression_attribute_values = {":reposSet": {"SS": repos_list}}

    return client.update_item(
        TableName=DDB_PROFILE_ANALYSIS_TABLE,
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )


def dynamodb_get_profile_analysis(user_id, **kwargs):
    """
    Get an item form the PROFILE_ANALYSIS table given the user's id
    """
    ddb = boto3.resource("dynamodb")

    table = ddb.Table(DDB_PROFILE_ANALYSIS_TABLE)
    response = table.get_item(Key={"uuid": str(user_id)}, **kwargs)
    return response["Item"]


def dynamodb_get_repo_analysis(repo_full_name, **kwargs):
    """
    Get an item from the repo analysis table given the repo_full_name
    """
    ddb = boto3.resource("dynamodb")

    table = ddb.Table(DDB_REPO_ANALYSIS_TABLE)
    response = table.get_item(Key={"full_name": repo_full_name}, **kwargs)
    return response.get("Item")


def trigger_analysis(user, github_token):
    """
    The core logic for Analyse mutation, performs checks and triggers the
    analysis mutation.

    Returns a dictionary with keys:
    1. success: bool
    2. errors: Optional[List[str]] - additional errors data in case success
    is False

    Does not create the ProfileAnalysis database object, that will have to be
    done manually from the mutations in which this is used
    """
    # Publish user id and github token to SNS topic
    try:
        response = publish_profile_analysis_trigger_to_sns(
            user.id, github_token
        )
        logger.info(
            "Message ID %s for profile analysis published to SNS topic"
            % response["MessageId"]
        )
    except botocore.exceptions.ClientError:
        logger.exception("AWS Boto error")
        return {"success": False, "errors": ["server error"]}

    # successfully triggered
    return {"success": True}


def invoke_initial_analysis_lambda(profile):
    # Convert to JSON and then to bytes
    payload = json.dumps(
        {
            "data": {
                "user_id": str(profile.user.id),
                f"{profile.provider}_access_token": profile.access_token,
            },
            "source": LAMBDA_INVOCATION_SOURCE,
        }
    ).encode()

    client = boto3.client("lambda")

    response = client.invoke(
        FunctionName=LAMBDA_INITIAL_ANALYSIS_FUNCTION,
        InvocationType="Event",
        Payload=payload,
    )

    # InvocationType | StatusCode
    # ---------------| ----------
    #   Synchronous  |   200
    #      Event     |   202
    #     Dry Run    |   204
    status_code = response.get("StatusCode")
    response_ok = status_code == 202

    if not response_ok:
        # This better be caught by Sentry - Add LoggingIntegration
        logger.warning(
            f"Lambda invocation returned unexpected code {status_code}. "
            f"Function: {LAMBDA_INITIAL_ANALYSIS_FUNCTION}. "
            f"Payload: {repr(payload)}"
        )

    return response_ok


def stack_overflow_get_user_data(token):
    payload = {
        "site": "stackoverflow",
        "access_token": token,
        "key": STACK_OVERFLOW_KEY,
    }

    url = f"{STACK_OVERFLOW_API_BASE_URL}/me"
    response = requests.get(
        url, headers={"Accept": "application/json"}, params=payload
    )

    if response.status_code == requests.codes.ok:
        data = response.json()
        print(data)

        # Note: The 'id' is actually the StackOverflow-specific 'user_id' and
        # not Stack Exchange's global 'account_id'
        return {
            "id": data["items"][0]["user_id"],
            "reputation": data["items"][0]["reputation"],
            "badge_counts": data["items"][0]["badge_counts"],
            "link": data["items"][0]["link"],
        }
    else:
        logger.error(
            "Error while fetching data from Stack Exchange API\n"
            f"Status Code: {response.status_code}\n"
            f"Response: {response.json()}"
        )
        return None
