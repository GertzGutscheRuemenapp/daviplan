import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User

from .models import Profile


class UserType(DjangoObjectType):
    class Meta:
        model = Profile
        fields = '__all__'

    user_name = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()

    def resolve_user_name(self, info):
        return self.user.username
    def resolve_email(self, info):
        return self.user.email
    def resolve_first_name(self, info):
        return self.user.first_name
    def resolve_last_name(self, info):
        return self.user.last_name


# ToDo: for test purposes only, replace with a mutation form?
# (because of name check and password double check -> response on fail)
class CreateUser(graphene.Mutation):
    class Arguments:
        user_name = graphene.String()
        password = graphene.String()

    user = graphene.Field(UserType)

    def mutate(root, info, user_name, password):
        user = User(username=user_name, password=password)
        user.save()
        profile = user.profile # auto created
        return CreateUser(user=profile)


# replace with mutation form?
class UserMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        user_name = graphene.String()
        email = graphene.String()
        first_name = graphene.String()
        last_name = graphene.String()
        password = graphene.String()
        admin_access = graphene.Boolean()
        can_create_scenarios = graphene.Boolean()
        can_edit_data = graphene.Boolean()

    user = graphene.Field(UserType)

    @classmethod
    def mutate(cls, root, info,
               id, user_name, email,
               first_name, last_name, password,
               admin_access, can_create_scenarios, can_edit_data):
        profile = Profile.objects.get(pk=id)
        user = profile.user
        user.username = user_name
        user.first_name = first_name
        user.last_name = last_name
        user.password = password
        profile.admin_access = admin_access
        profile.can_create_scenarios = can_create_scenarios
        profile.can_edit_data = can_edit_data
        # profile is saved automatically on user save
        user.save()
        return UserMutation(user=user)


class Query(graphene.ObjectType):
    all_users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.ID())

    def resolve_all_users(self, info, *args):
        return Profile.objects.all()

    def resolve_user(self, info, id):
        return Profile.objects.get(pk=id)


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_user = UserMutation.Field()