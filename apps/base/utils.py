import logging
import typing

import boto3

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

logger = logging.getLogger(__name__)


class CreateModelResult(typing.NamedTuple):
    success: bool
    object: typing.Optional[models.Model] = None
    errors: typing.Optional[typing.List[str]] = None


class GetModelResult(typing.NamedTuple):
    success: bool
    object: typing.Optional[models.Model] = None
    errors: typing.Optional[typing.List[str]] = None


def create_model_object(
    model: typing.Type[models.Model], **kwargs: typing.Any
) -> CreateModelResult:
    """
    Attempts to create a model object. Runs validations and returns a
    `CreateModelResult` instance.

    Parameters:
    * model {models.Model class}: The model for which the object is to be
    created
    * kwargs {keyword arguments}: The kwargs to be fed to the model class while
    creating the object

    Returns:
    * result {CreateModelResult}: A `CreateModelResult` object with the
    `success` attribute denoting whether creation was successful or not. If
    success is True, `result.object` will be the newly created object. If it is
    False, `result.errors` will have the corresponding list of error messages
    """
    object = model(**kwargs)

    try:
        # Run validations
        object.full_clean()
    except ValidationError as e:
        return CreateModelResult(success=False, errors=get_error_messages(e))

    object.save()
    return CreateModelResult(success=True, object=object)


def get_model_object(
    model: typing.Type[models.Model], **kwargs: typing.Any
) -> GetModelResult:
    """
    Tries to get a model with given kwargs. Handles DoesNotExist and
    MultipleObjectsReturned exceptions

    Parameters:
    * model {models.Model class}: The model from which the object is to be
    fetched
    * kwargs: The conditions to be used while getting the model object

    Returns:
    * result {GetModelResult}: A `GetModelResult` object will be returned with
    `result.success` corresponding to whether the get operation was successful.
    If success is True, `result.object` will be the required object. If the
    operation was not successful due to a DoesNotExist or a
    MultipleObjectsReturned exception, `result.errors` will have the
    corresponding error messages list.
    """
    try:
        object = model.objects.get(**kwargs)
    except model.DoesNotExist:
        errors = [f"{model.__name__} with given query {kwargs} does not exist"]
        return GetModelResult(success=False, errors=errors)
    except model.MultipleObjectsReturned:
        errors = [
            f"{model.__name__} with given query {kwargs} "
            "returned multiple results"
        ]
        return GetModelResult(success=False, errors=errors)
    except ValidationError as e:
        return GetModelResult(success=False, errors=get_error_messages(e))

    return GetModelResult(success=True, object=object)


def get_error_message(error: Exception) -> str:
    """Obtains the error message for an Exception.

    Procedure:
    1. See if exception has a 'message' attribute. If yes, return that.
    2. Otherwise simply return `str(error)`
    """
    return getattr(error, "message", str(error))


def get_error_messages(error: Exception) -> typing.List[str]:
    """An extension to the `get_error_message` util.
    Sometimes some erros (specifically Django `ValidationError`s) may return a
    list of error messages instead of a single message.

    This method handles both the cases and returns a list of error(s).
    """
    return getattr(error, "messages", [get_error_message(error)])


def get_sentinel_user():
    UserModel = get_user_model()

    try:
        sentinel_user = UserModel.objects.get(username="ghost")
    except UserModel.DoesNotExist:
        sentinel_user = UserModel(
            username="ghost",
            first_name="deleted",
            last_name="user",
            email="ghost@hyperlog.io",
        )
        sentinel_user.set_unusable_password()
        sentinel_user.save()

    return sentinel_user


def full_clean_and_save(obj: models.Model) -> typing.Union[Exception, None]:
    try:
        obj.full_clean()
        obj.save()
    except ValidationError as e:
        return e


# General AWS utils


def get_aws_client(resource, **kwargs):
    """Returns a Boto3 client for the given resource.

    Parameters:
    * resource {str}: The AWS resource to fetch the client for
    (e.g. "sqs", "sns")
    * kwargs {Dict[str, Any]}: Other parameters while connecting the client
    which will overwrite the default configuration (from env variables).

    Returns:
    client {Boto3 low-level client}: A boto3 low-level client to access the
    provided resource
    """
    # Credentials and config details will automatically be taken from
    # environment variables
    try:
        client = boto3.client(resource)
        return client
    except Exception as e:
        logger.error(e, exc_info=True)
        raise


# SNS specific utils


def get_or_create_sns_topic_by_topic_name(topic_name):
    """
    Creates a new SNS topic and returns a SNS.Topic object.
    This is idempotent, topic will only be created if it does not exist.

    Parameters:
    * topic_name {str}: The name of the topic

    Returns:
    * {SNS.Topic}: A Topic object of the SNS service resource
    """
    sns = boto3.resource("sns")
    return sns.create_topic(Name=topic_name)


# SQS


def get_sqs_queue_by_name(queue_name):
    """
    Gets a SQS queue by the name queue_name.

    Parameters:
    * queue_name {str}: Name of the SQS queue

    Returns:
    * queue {boto3 SQS Queue}: The boto3 queue object with the name queue_name

    Note: Raises a `botocore.exceptions.ClientError` if queue does not exist
    """
    sqs = boto3.resource("sqs")
    return sqs.get_queue_by_name(QueueName=queue_name)


def create_sqs_queue(queue_name, attributes=None, tags=None):
    """
    Create a SQS queue with the name `queue_name`

    Parameters:
    * queue_name {str}: The name of the queue
    * attributes {Dict[str, Any]}: The Attributes mapping.
    * tags {Dict[str, Any]}: Associated tags

    See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html  # noqa

    Returns:
    * queue {boto3 SQS Queue}: The new boto3 queue with the given name

    Note: Raises a `botocore.exceptions.ClientError` if queue already exists
    """
    sqs = boto3.resource("sqs")
    return sqs.create_queue(
        QueueName=queue_name, Attributes=attributes, Tags=tags
    )
