import logging

import botocore

from django.conf import settings
from django.shortcuts import render
from django.utils import timezone

from apps.base.utils import (
    create_model_object,
    get_aws_client,
    get_sqs_queue_by_name,
)

DYNAMODB_PROFILES_TABLE_NAME = settings.AWS_DYNAMODB_PROFILES_TABLE
DYNAMODB_PROFILE_ANALYSIS_TABLE = settings.AWS_DYNAMODB_PROFILE_ANALYSIS_TABLE
PROFILE_ANALYSIS_QUEUE_NAME = settings.AWS_PROFILE_ANALYSIS_QUEUE

GITHUB_SUCCESS_TEMPLATE_PATH = "profiles/github_success.html"
GITHUB_FAIL_TEMPLATE_PATH = "profiles/github_fail.html"


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
        TableName=DYNAMODB_PROFILES_TABLE_NAME,
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
    )


def dynamodb_get_profile(user_id):
    """
    Uses the DynamoDB GetItem API to get the profile data as per the "profiles"
    table in raw format as returned by boto3
    """
    client = get_aws_client("dynamodb")

    key = {"user_id": {"S": str(user_id)}}
    response = client.get_item(TableName=DYNAMODB_PROFILES_TABLE_NAME, Key=key)
    return response["Item"]


def string_to_int_or_float(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


def dynamodb_process_boto_val(boto_val):
    if "S" in boto_val:
        return str(boto_val["S"])

    elif "N" in boto_val:
        return string_to_int_or_float(boto_val["N"])

    elif "B" in boto_val:
        return bytes(boto_val["B"])

    elif "BOOL" in boto_val:
        return bool(boto_val["BOOL"])

    elif "NULL" in boto_val:
        return None

    elif "SS" in boto_val:
        return [str(val) for val in boto_val["SS"]]

    elif "NS" in boto_val:
        return [string_to_int_or_float(val) for val in boto_val["NS"]]

    elif "BS" in boto_val:
        return [bytes(val) for val in boto_val["BS"]]

    elif "M" in boto_val:
        return dynamodb_convert_boto_dict_to_python_dict(boto_val["M"])

    elif "L" in boto_val:
        return [dynamodb_process_boto_val(val) for val in boto_val["L"]]

    else:
        raise Exception("Unexpected data format: %s" % str(boto_val))


def dynamodb_convert_boto_dict_to_python_dict(boto_dict):
    """
    Converts a boto3 representation for a DynamoDB item into a python object
    """
    python_dict = {}

    for (key, boto_val) in boto_dict.items():
        python_dict[key] = dynamodb_process_boto_val(boto_val)

    return python_dict


def push_profile_analysis_to_sqs_queue(user_id, github_token):
    """
    Push a task for profile analysis onto the SQS profile analysis queue
    """
    queue = get_sqs_queue_by_name(PROFILE_ANALYSIS_QUEUE_NAME)

    # The MessageBody argument is required. Use it for timestamp
    return queue.send_message(
        MessageBody=str(timezone.now().timestamp()),
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
            dynamodb_create_or_update_profile(profile_creation.object)
        except botocore.exceptions.ClientError:
            logger.error("DynamoDB exception encountered", exc_info=True)

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
        TableName=DYNAMODB_PROFILE_ANALYSIS_TABLE,
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )
