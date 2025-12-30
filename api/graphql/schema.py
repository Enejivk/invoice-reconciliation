"""GraphQL schema."""
import strawberry

from api.graphql.queries import Query
from api.graphql.mutations import Mutation


schema = strawberry.Schema(query=Query, mutation=Mutation)

