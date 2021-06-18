from .user.schema import Query as UserQuery
from graphene import ObjectType, Schema

class Query(UserQuery, ObjectType):
    pass

schema = Schema(query=Query)