import graphene
from graphql import GraphQLError
from django.utils.translation import gettext as _
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
import graphql_jwt
from graphql_jwt.decorators import login_required

from .models import Profile


class Authentication(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


class UserType(DjangoObjectType):
    class Meta:
        model = Profile
        fields = '__all__'

    user_name = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    is_superuser = graphene.Boolean()

    def resolve_user_name(self, info):
        return self.user.username
    def resolve_email(self, info):
        return self.user.email
    def resolve_first_name(self, info):
        return self.user.first_name
    def resolve_last_name(self, info):
        return self.user.last_name
    def resolve_is_superuser(self, info):
        return self.user.is_superuser


# ToDo: for test purposes only, replace with a mutation form?
# (because of name check and password double check -> response on fail)
class CreateUser(graphene.Mutation):
    class Arguments:
        user_name = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()
    user = graphene.Field(UserType)

    @login_required
    def mutate(root, info, user_name, password):
        try:
            User.objects.get(username=user_name)
            raise GraphQLError(_('Nutzername ist bereits vergeben'))
        except User.DoesNotExist:
            pass
        user = User(username=user_name, password=password)
        user.save()
        profile = user.profile # auto created
        return CreateUser(user=profile, ok=True)


# replace with mutation form?
class UpdateUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        user_name = graphene.String(required=False)
        email = graphene.String(required=False)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        password = graphene.String(required=False)
        admin_access = graphene.Boolean(required=False)
        can_create_scenarios = graphene.Boolean(required=False)
        can_edit_data = graphene.Boolean(required=False)

    user = graphene.Field(UserType)

    @classmethod
    @login_required
    def mutate(cls, root, info, id, **kwargs):
        profile = Profile.objects.get(pk=id)
        user = profile.user
        if 'user_name' in kwargs:
            try:
                ex_user = User.objects.get(username=kwargs['user_name'])
                if ex_user.id != user.id:
                    raise GraphQLError(_('Nutzername ist bereits vergeben'))
            except User.DoesNotExist:
                pass
            user.username = kwargs['user_name']
        for attr in ['first_name', 'last_name', 'password', 'email']:
            if attr in kwargs:
                setattr(user, attr, kwargs[attr])
        for attr in ['admin_access', 'can_create_scenarios', 'can_edit_data']:
            if attr in kwargs:
                setattr(profile, attr, kwargs[attr])
        # profile is saved automatically on user save
        user.save()
        return UpdateUser(user=profile)


class DeleteUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    ok = graphene.Boolean()

    @classmethod
    @login_required
    def mutate(cls, root, info, id):
        user = User.objects.get(profile__pk=id)
        if user.is_superuser:
            return DeleteUser(ok=False)
        user.delete()
        return DeleteUser(ok=True)


class Query(graphene.ObjectType):
    all_users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.ID())
    whoami = graphene.Field(UserType)

    @login_required
    def resolve_whoami(self, info, **kwargs):
        return info.context.user.profile

    @login_required
    def resolve_all_users(self, info, *args):
        return Profile.objects.all()

    @login_required
    def resolve_user(self, info, id):
        return Profile.objects.get(pk=id)


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()