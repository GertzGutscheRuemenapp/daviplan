import { NgModule } from "@angular/core";
import { HttpClientModule } from "@angular/common/http";
// Apollo
import { Apollo, APOLLO_OPTIONS } from 'apollo-angular';
import { HttpLink } from "apollo-angular/http";
import { InMemoryCache, ApolloLink } from "@apollo/client/core";
import { setContext } from '@apollo/client/link/context';

export const uri = 'http://localhost:8000/graphql';

export function createApollo(httpLink: HttpLink) {
  const basic = setContext((operation, context) => ({
    headers: {
      Accept: 'charset=utf-8'
    }
  }));

  const auth = setContext((operation, context) => {
    const token = localStorage.getItem('token');

    if (token === null) {
      return {};
    } else {
      return {
        headers: {
          Authorization: token? `JWT ${token}`: null
        }
      };
    }
  });

  const link = ApolloLink.from([basic, auth, httpLink.create({ uri })]);
  const cache = new InMemoryCache();

  return {
    link,
    cache
  }
}

@NgModule({
  exports: [HttpClientModule],
  providers: [{
    provide: APOLLO_OPTIONS,
    useFactory: createApollo,
    deps: [HttpLink]
  }]
})

export class GraphQLModule {}
