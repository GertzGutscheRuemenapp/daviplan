import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable, ReplaySubject, Subject, of, BehaviorSubject, throwError, Subscription } from 'rxjs';
import { User } from "./rest-interfaces";
import { catchError, filter, switchMap, take, tap, delay, share } from 'rxjs/operators';
import { RestAPI } from "./rest-api";
import {
  CanActivate,
  ActivatedRouteSnapshot,
  UrlTree,
  Router
} from "@angular/router";
import { SettingsService, SiteSettings } from "./settings.service";

interface Token {
  access: string;
  refresh: string;
}

@Injectable({ providedIn: 'root' })
/**
 * token authentication service to login and verify user at backend API
 * access token is regularly rotated (access token lifetime is defined in backend)
 *
 */
export class AuthService {
  // private anonymous: User = { id: , name: 'anonym', };
  user$ = new BehaviorSubject<User | undefined>(undefined);
  private timer?: Subscription;

  constructor(private rest: RestAPI, private http: HttpClient, private router: Router, public settings: SettingsService) { }

  private setLocalStorage(token: Token) {
    localStorage.setItem('accessToken', token.access);
    localStorage.setItem('refreshToken', token.refresh);
  }

  private clearLocalStorage() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  }

  /**
   * login at backend API with given credentials (username and password)
   *
   * @param credentials
   */
  login(credentials: { username: string; password?: string }): Observable<Token> {
    let query = this.http.post<Token>(this.rest.URLS.token, credentials)
      .pipe(
        tap(token => {
          this.setLocalStorage(token);
          this.startTokenTimer();
          this.fetchCurrentUser().subscribe(user=>this.user$.next(user));
        })
      );
      return query;
  }

  /**
   * log out at backend, token will be removed
   * redirects to login page
   */
  logout(): void {
    this.clearLocalStorage();
    this.stopTokenTimer();
    this.user$.next(undefined);
    if (!this.settings.siteSettings$.value?.demoMode)
      this.router.navigateByUrl('/login');
  }

  /**
   * get user information (cached)
   */
  getCurrentUser(): Observable<User | undefined> {
    return this.user$.pipe(
      switchMap(user => {
        // check if we already have user data
        if (user) {
          return of(user);
        }
        const token = localStorage.getItem('accessToken');
        // if there is token then fetch the current user
        if (token) {// || this.settings.siteSettings$.value.demoMode) {
          return this.fetchCurrentUser();
        }
        return of(undefined);
      })
    );
  }

  /**
   * fetch user information from backend
   */
  fetchCurrentUser(): Observable<User | undefined> {
    return this.http.get<User>(this.rest.URLS.currentUser)
      .pipe(
        catchError(err => {
          this.logout();
          return of(undefined);
        }),
        tap(user => {
          this.user$.next(user);
        })
      );
  }

  hasPreviousLogin(): boolean {
    const refreshToken = localStorage.getItem('refreshToken');
    return !!refreshToken;
  }

  /**
   * refresh the access token with the refresh token
   * initiates the next refresh cycle
   */
  refreshToken(): Observable<Token> {
    const refreshToken = localStorage.getItem('refreshToken');
    return this.http.post<Token>(
      this.rest.URLS.refreshToken,{ refresh: refreshToken }
    ).pipe(
      tap(token => {
        this.setLocalStorage(token);
        this.startTokenTimer();
      })
    );
  }

  // get remaining time before access token expires
  private getTokenRemainingTime() {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
      return 0;
    }
    const jwtToken = JSON.parse(atob(accessToken.split('.')[1]));
    const expires = new Date(jwtToken.exp * 1000);
    return expires.getTime() - Date.now();
  }

  // auto refresh access token after it is expired
  private startTokenTimer() {
    const timeout = this.getTokenRemainingTime();
    if (this.timer || !timeout) this.stopTokenTimer();
    this.timer = of(true)
      .pipe(
        delay(timeout),
        tap({
          next: () => this.refreshToken().subscribe(),
        })
      )
      .subscribe();
  }

  private stopTokenTimer() {
    this.timer?.unsubscribe();
    this.timer = undefined;
  }
}

@Injectable()
/**
 * Interceptor adds (rotated) token verification to http calls (required by backend API)
 */
export class TokenInterceptor implements HttpInterceptor {
  private refreshingInProgress: boolean = false;
  private accessTokenSubject: Subject<string> = new ReplaySubject<string>();
  constructor(private authService: AuthService, private router: Router) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const accessToken = localStorage.getItem('accessToken');

    return next.handle(this.addAuthorizationHeader(req, accessToken || '')).pipe(
      catchError(err => {
        //
        if (err instanceof HttpErrorResponse && err.status === 401) {
          // get refresh tokens
          const refreshToken = localStorage.getItem('refreshToken');
          if (refreshToken && accessToken) {
            return this.refreshToken(req, next);
          }
          // return this.logout(err);
        }
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

  private logout(err: any): Observable<HttpEvent<any>> {
    this.authService.logout();
    return throwError(err);
  }

  private refreshToken(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // get new token, if no refreshing is in progress
    if (!this.refreshingInProgress) {
      this.refreshingInProgress = true;
      localStorage.removeItem('accessToken');
      return this.authService.refreshToken().pipe(
        switchMap((res) => {
          this.refreshingInProgress = false;
          this.accessTokenSubject.next(res.access);
          // repeat failed request with new token
          return next.handle(this.addAuthorizationHeader(request, res.access));
        }),
        catchError(err => {
          this.refreshingInProgress = false;
          return throwError(err);
          //return this.logout(err);
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
/**
 * protects routes based on user permissions
 * by default blocks all calls if user is not logged in
 * pass "data" property with entry "expectedRole" (value: admin or dataEditor) to block route from other users
 * role admin includes access to dataEditor pages
 */
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) { }

  canActivate(next: ActivatedRouteSnapshot): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.authService.settings.getSiteSettings().pipe(switchMap(settings => {
      // all pages are accessible in "demo mode"
      if (settings.demoMode)
        return of(true);
      return this.authService.getCurrentUser().pipe(switchMap(user => {
        const expectedRole = next.data.expectedRole;
        const isLoggedIn = !!user;
        if (expectedRole === 'admin')
          return of(isLoggedIn && (user?.profile.adminAccess || user?.isSuperuser));
        if (expectedRole === 'dataEditor')
          return of(isLoggedIn && (user?.profile.canEditBasedata || user?.profile.adminAccess || user?.isSuperuser));
        return of(isLoggedIn);
      }))
    }), tap(hasAccess => {
          if (!hasAccess) {
            // @ts-ignore
            const _next = next._routerState.url;
            let params: any = {};
            if (_next && _next !== '/') params['queryParams'] = {next: _next};
            if (!this.authService.settings.siteSettings$.value?.demoMode)
              this.router.navigate(['/login'], params);
          }
        }));
  }
}
