import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.base.models import CICharField, CIEmailField


def password_login_type():
    return {"password": True}


def default_social_links():
    return {}


def validate_social_links(val):
    for key in val.keys():
        if key not in User.SUPPORTED_SOCIAL_LINKS:
            raise ValidationError("Unknown social link provider %s" % key)


def validate_setup_step(val):
    if val != User.SETUP_COMPLETED_STEP and (
        val < User.MIN_SETUP_STEP or val > User.MAX_SETUP_STEP
    ):
        raise ValidationError(f"Invalid value for setup step {val}")


class UserManager(BaseUserManager):
    def _create_user(
        self, username, email, password, is_staff, is_superuser, **extra_fields
    ):
        """
        Creates and saves a User with the given username, email and password.
        """
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            is_active=True,
            is_staff=is_staff,
            is_superuser=is_superuser,
            last_login=timezone.now(),
            registered_at=timezone.now(),
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, username=None, email=None, password=None, **extra_fields
    ):
        is_staff = extra_fields.pop("is_staff", False)
        is_superuser = extra_fields.pop("is_superuser", False)
        return self._create_user(
            username, email, password, is_staff, is_superuser, **extra_fields
        )

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(
            username,
            email,
            password,
            is_staff=True,
            is_superuser=True,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    """
    `setup_step` field: Can be between 0 to 4, such that:
    0 - All steps completed
    1 - User signed up
    2 - User has completed all connections
    3 - User has added all required information
    4 - User has connected the required repositories
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = CICharField(
        verbose_name="Username",
        unique=True,
        max_length=30,
        validators=[UnicodeUsernameValidator()],
        error_messages={"unique": "A user with that username already exists"},
    )
    email = CIEmailField(
        verbose_name="Email",
        unique=True,
        max_length=255,
        error_messages={"unique": "A user with that email id already exists"},
    )
    first_name = models.CharField(
        verbose_name="First name", max_length=30, default="first"
    )
    last_name = models.CharField(
        verbose_name="Last name", max_length=30, blank=True,
    )

    is_admin = models.BooleanField(verbose_name="Admin", default=False)
    is_active = models.BooleanField(verbose_name="Active", default=True)
    is_staff = models.BooleanField(verbose_name="Staff", default=False)
    is_enrolled_for_mails = models.BooleanField(
        verbose_name="Enrolled in mailing list", default=True
    )
    registered_at = models.DateTimeField(
        verbose_name="Registered at", auto_now_add=timezone.now
    )

    new_user = models.BooleanField(verbose_name="New User", default=False)
    login_types = JSONField(default=password_login_type)
    tagline = models.CharField(max_length=255, blank=True)
    social_links = JSONField(
        default=default_social_links,
        blank=True,
        validators=[validate_social_links],
    )
    about = models.TextField(verbose_name="About information", blank=True)
    theme_code = models.CharField(
        verbose_name="Theme Code", max_length=64, default="default",
    )
    show_avatar = models.BooleanField(
        verbose_name="Display Avatar on Portfolio", default=True,
    )
    under_construction = models.BooleanField(
        verbose_name="Portfolio under construction", default=True,
    )
    setup_step = models.IntegerField(
        verbose_name="Current setup step", default=1
    )

    # Supported SOCIAL_LINKS for social links JSON
    SUPPORTED_SOCIAL_LINKS = [
        "twitter",
        "facebook",
        "github",
        "stackoverflow",
        "dribble",
        "devto",
        "linkedin",
    ]

    SETUP_COMPLETED_STEP = 0
    MIN_SETUP_STEP = 1
    MAX_SETUP_STEP = 4

    # Fields settings
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"

    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    full_name.fget.short_description = "Full name"

    @property
    def short_name(self):
        return f"{self.last_name} {self.first_name[0]}."

    short_name.fget.short_description = "Short name"

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.short_name

    def __str__(self):
        return self.full_name

    def set_password(self, raw_password):
        """Overriding to set "password" key in user.login_types to True"""
        if raw_password is not None:
            self.login_types["password"] = True

        return super().set_password(raw_password)


class DeletedUser(models.Model):
    username = models.CharField(verbose_name="Username", max_length=30)
    email = models.EmailField(verbose_name="Email", max_length=255)
    first_name = models.CharField(verbose_name="First name", max_length=30)
    last_name = models.CharField(verbose_name="Last name", max_length=30)

    is_admin = models.BooleanField(verbose_name="Admin", default=False)
    is_active = models.BooleanField(verbose_name="Active", default=True)
    is_staff = models.BooleanField(verbose_name="Staff", default=False)
    registered_at = models.DateTimeField(verbose_name="Registered at")

    new_user = models.BooleanField(verbose_name="New User", default=False)
    login_types = JSONField(default=password_login_type)
    tagline = models.CharField(max_length=255, blank=True)
    social_links = JSONField(default=default_social_links, blank=True)
    about_page = models.TextField(verbose_name="About Page", blank=True)
    theme_code = models.CharField(
        verbose_name="Theme Code", max_length=64, default="default",
    )
    show_avatar = models.BooleanField(
        verbose_name="Display Avatar on Portfolio", default=True,
    )
    under_construction = models.BooleanField(
        verbose_name="Portfolio under construction", default=True,
    )
    setup_step = models.IntegerField(
        verbose_name="Current setup step", default=1
    )

    # Fields specific to DeletedUser
    old_user_id = models.UUIDField(verbose_name="Old User ID")
    deleted_at = models.DateTimeField(
        verbose_name="Deleted at", auto_now_add=timezone.now
    )

    class Meta:
        verbose_name = "Deleted User"
        verbose_name_plural = "Deleted Users"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    full_name.fget.short_description = "Full name"

    @property
    def short_name(self):
        return f"{self.last_name} {self.first_name[0]}."

    short_name.fget.short_description = "Short name"

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.short_name

    def __str__(self):
        return self.full_name
