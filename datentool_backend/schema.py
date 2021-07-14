from .user import schema as user_schema
from graphene import ObjectType, Schema


class MergedQueries(user_schema.Query, ObjectType):
    '''to merge queries from individual schemes add them to the list of super
    classes here'''


class MergedMutations(user_schema.Authentication, user_schema.Mutation,
                      ObjectType):
    '''to merge mutations from individual schemes add them to the list of super
    classes here'''


# merged schema
schema = Schema(query=MergedQueries, mutation=MergedMutations)