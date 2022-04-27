import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable, ReplaySubject, Subject, of, BehaviorSubject, throwError } from 'rxjs';
import { User } from './pages/login/users';
import { catchError, filter, switchMap, take, tap, map } from 'rxjs/operators';
import { RestAPI } from "./rest-api";
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree, Router } from "@angular/router";

interface Token {
  access: string;
  refresh: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  user$ = new BehaviorSubject<User | undefined>(undefined);

  constructor(private rest: RestAPI, private http: HttpClient) { }

  login(credentials: { username: string; password: string }): Observable<Token> {
    // localStorage.removeItem('token');
    let query = this.http.post<Token>(this.rest.URLS.token, credentials)
      .pipe(
        tap(token => {
          localStorage.setItem('token', token.access);
          localStorage.setItem('refreshToken', token.refresh);
          this.fetchCurrentUser().subscribe(user=>this.user$.next(user));
        })
      );
      return query;
  }

  getCurrentUser(): Observable<User | undefined> {
    return this.user$.pipe(
      switchMap(user => {
        // check if we already have user data
        if (user) {
          return of(user);
        }

        const token = localStorage.getItem('token');
        // if there is token then fetch the current user
        if (token) {
          return this.fetchCurrentUser();
        }

        return of(undefined);
      })
    );
  }

  fetchCurrentUser(): Observable<User | undefined> {
    return this.http.get<User>(this.rest.URLS.currentUser)
      .pipe(
        catchError(err => {
          return of(undefined);
        }),
        tap(user => {
          this.user$.next(user);
        })
      );
  }

  refreshToken(): Observable<Token> {
    const refreshToken = localStorage.getItem('refreshToken');
    // localStorage.removeItem('token');
    return this.http.post<Token>(
      this.rest.URLS.refreshToken,{ refresh: refreshToken }
    ).pipe(
      tap(token => {
        localStorage.setItem('token', token.access);
        localStorage.setItem('refreshToken', token.refresh);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    this.user$.next(undefined);
  }
}

@Injectable()
export class TokenInterceptor implements HttpInterceptor {
  private refreshingInProgress: boolean = false;
  private accessTokenSubject: Subject<string> = new ReplaySubject<string>();

  constructor( private authService: AuthService, private router: Router) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const accessToken = localStorage.getItem('token');

    return next.handle(this.addAuthorizationHeader(req, accessToken || '')).pipe(
      catchError(err => {
        //
        if (err instanceof HttpErrorResponse && err.status === 401) {
          // get refresh tokens
          const refreshToken = localStorage.getItem('refreshToken');
          if (refreshToken && accessToken) {
            return this.refreshToken(req, next);
          }
          return this.logoutAndRedirect(err);
        }
        // if (err instanceof HttpErrorResponse && err.status === 403) {
        //   return this.logoutAndRedirect(err);
        // }
        // other errors
        return throwError(err);
      })
    );
  }

  private addAuthorizationHeader(request: HttpRequest<any>, token: string): HttpRequest<any> {
    if (token) {
      return request.clone({setHeaders: {Authorization: `Bearer ${token}`}});
    }
    return request;
  }

  private logoutAndRedirect(err: any): Observable<HttpEvent<any>> {
    this.authService.logout();
    this.router.navigateByUrl('/login');
    return throwError(err);
  }

  private refreshToken(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // get new token, if no refreshing is in progress
    if (!this.refreshingInProgress) {
      this.refreshingInProgress = true;
      localStorage.removeItem('token');
      return this.authService.refreshToken().pipe(
        switchMap((res) => {
          this.refreshingInProgress = false;
          this.accessTokenSubject.next(res.access);
          // repeat failed request with new token
          return next.handle(this.addAuthorizationHeader(request, res.access));
        }),
        catchError(err => {
          this.refreshingInProgress = false;
          return this.logoutAndRedirect(err);
        })
      );
    }
    // refresh already in progress -> wait for token
    else {
      return this.accessTokenSubject.pipe(
        filter(token => token !== null),
        take(1),
        switchMap(token => {
          // repeat failed request with new token
          return next.handle(this.addAuthorizationHeader(request, token));
        }));
    }
  }
}

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService,
              private router: Router) { }

  canActivate(
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.authService.getCurrentUser().pipe(
      map(user => {
        const expectedRole = next.data.expectedRole;
        const isLoggedIn = !!user;
        if (expectedRole === 'admin')
          return isLoggedIn && (user?.profile.adminAccess || user?.isSuperuser);
        if (expectedRole === 'dataEditor')
          return isLoggedIn && (user?.profile.canEditBasedata || user?.profile.adminAccess || user?.isSuperuser);
        return isLoggedIn;
      }),
      tap(hasAccess => {
        if (!hasAccess) {
          this.router.navigateByUrl('/login');
        }
      })
    );
  }
}
