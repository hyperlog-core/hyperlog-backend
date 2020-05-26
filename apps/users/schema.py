import graphene
import graphql_jwt
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from django.contrib.auth import logout

from apps.users.models import User


class UserType(DjangoObjectType):
    class Meta:
        model = User
        only_fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "registered_at",
            "profiles",
        ]


class Query(graphene.ObjectType):
    user = graphene.Field(UserType, id=graphene.Int(required=True))
    users = graphene.List(UserType)
    this_user = graphene.Field(UserType)

    @staticmethod
    def resolve_user(cls, info, **kwargs):
        return User.objects.get(id=kwargs.get("id"))

    @staticmethod
    def resolve_users(cls, info, **kwargs):
        return User.objects.all()

    @staticmethod
    @login_required
    def resolve_this_user(cls, info, **kwargs):
        if info.context.user.is_authenticated:
            return info.context.user


class Register(graphene.Mutation):
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    class Arguments:
        email = graphene.String(required=True)
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)

    def mutate(self, info, email, username, password, first_name, last_name):
        if User.objects.filter(email__iexact=email).exists():
            errors = ["emailAlreadyExists"]
            return Register(success=False, errors=errors)

        if User.objects.filter(username__iexact=username).exists():
            errors = ["usernameAlreadyExists"]
            return Register(success=False, errors=errors)

        # create user
        user = User.objects.create(
            username=username,
            email=email,
            last_name=last_name,
            first_name=first_name,
        )
        user.set_password(password)
        user.save()
        return Register(success=True)


class Logout(graphene.Mutation):
    """ Mutation to logout a user """

    success = graphene.Boolean()

    def mutate(self, info):
        logout(info.context)
        return Logout(success=True)


class Mutation(object):
    login = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    register = Register.Field()
    logout = Logout.Field()
