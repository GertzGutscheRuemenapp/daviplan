import graphene
from graphene_django import DjangoObjectType
from .models import Profile


class UserType(DjangoObjectType):
    class Meta:
        model = Profile
        #fields = '__all__'
        fields = ('id', 'admin_access', 'can_create_scenarios', 'can_edit_data')

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


class Query(graphene.ObjectType):
    all_users = graphene.List(UserType)
    user = graphene.Field(UserType, user_id=graphene.ID())

    def resolve_all_users(self, info, *args):
        return Profile.objects.all()

    def resolve_user(self, info, user_id):
        return Profile.objects.get(pk=user_id)