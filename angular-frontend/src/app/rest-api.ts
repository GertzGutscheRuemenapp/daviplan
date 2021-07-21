import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class RestAPI {
  public readonly API_SERVER = '';
  public readonly API_ENDPOINT = `${ this.API_SERVER }/api`;
  public readonly URLS = {
    token: `${ this.API_ENDPOINT }/token/`,
    refreshToken: `${ this.API_ENDPOINT }/token/refresh/`,
    users: `${ this.API_ENDPOINT }/users/`,
    currentUser: `${ this.API_ENDPOINT }/users/current/`
  }
  // ToDo: functions with generalized HTTP calls in here
}
