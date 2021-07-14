
import { Injectable } from '@angular/core';
import { gql } from 'graphql-tag';
import { Apollo, QueryRef } from 'apollo-angular';
import { Observable, ReplaySubject, Subject, of} from 'rxjs';
import { User } from './administration/users/users';
import { map, switchMap, tap } from 'rxjs/operators';

interface Token {
  token: string;
  refreshToken: string;
  payload: {
    username: string;
  };
}

interface LoginResponse {
  tokenAuth: Token
}

interface WhoAmI {
  whoami: User
}

const LOGIN_QUERY = gql`
  mutation TokenAuth($username: String!, $password: String!) {
    tokenAuth(username: $username, password: $password) {
      token, payload, refreshToken
    }
}
`;

const REFRESH_QUERY = gql`
  mutation RefreshToken($refreshToken: String!) {
    refreshToken(refreshToken: $refreshToken) {
      token, payload, refreshToken
    }
}
`;

const USER_QUERY = gql`
  query {
    whoami {
        id, userName, email, firstName, lastName,
        canEditData, canCreateScenarios, adminAccess, isSuperuser
    }
}
`;

@Injectable({
  providedIn: 'root'
})

export class AuthService {

  constructor(private apollo: Apollo) { }
  // user$ = new BehaviorSubject(null as any);
  user$: Subject<User> = new ReplaySubject<User>()

  login(credentials: { username: string; password: string }): Observable<any> {
    localStorage.removeItem('token');
    let query = this.apollo.mutate<{ tokenAuth: Token }>({
      mutation: LOGIN_QUERY,
      variables: {
        password: credentials.password,
        username: credentials.username
      }
    })
    query.pipe(tap (({ data }) => {
      if (data){
        localStorage.setItem('user', data.tokenAuth.payload.username);
        localStorage.setItem('token', data.tokenAuth.token);
        localStorage.setItem('refreshToken', data.tokenAuth.refreshToken);
        this.fetchCurrentUser();
      }
    }));
    return query;
  }

  getCurrentUser(): Observable<User> {
    let user = this.user$.pipe(
      switchMap(user => {
        if (user) {
          return of(user);
        }

        const token = localStorage.getItem('token');
        // if there is token then fetch the current user
        if (token) {
          return this.fetchCurrentUser();
        }

        return of(null);
      })
    );
    return user as Observable<User>;
  }

  fetchCurrentUser(): Observable<User> {
    let query = this.apollo.watchQuery<WhoAmI>({ query: USER_QUERY }).valueChanges;
    query.subscribe((response)=>{
      this.user$.next(response.data.whoami);
    })
    return query.pipe(map(({ data }) => data.whoami));
  }

  refreshToken(): Observable<string> {
    const refreshToken = localStorage.getItem('refreshToken');
    localStorage.removeItem('token');
    let query = this.apollo.mutate<{ refreshToken: Token }>({
      mutation: LOGIN_QUERY,
      variables: {
        password: refreshToken,
      }
    });
    query.pipe(tap (({ data }) => {
      if (data){
        localStorage.setItem('token', data!.refreshToken.token);
        localStorage.setItem('refreshToken', data!.refreshToken.refreshToken);
      }
    }));
    return query.pipe(map(({ data }) => data!.refreshToken.refreshToken));
  }

  logout(): void {
    this.user$.next();
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    this.apollo.client.resetStore();
  }

}
