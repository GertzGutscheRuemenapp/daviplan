import { Injectable } from '@angular/core';
import { environment } from "../environments/environment";

@Injectable({
  providedIn: 'root'
})
export class RestAPI {
  public readonly API_ENDPOINT = environment.apiPath;
  public readonly URLS = {
    token: `${ this.API_ENDPOINT }/token/`,
    refreshToken: `${ this.API_ENDPOINT }/token/refresh/`,
    users: `${ this.API_ENDPOINT }/users/`,
    currentUser: `${ this.API_ENDPOINT }/users/current/`,
    settings: `${ this.API_ENDPOINT }/settings/default/`,
    projectSettings: `${ this.API_ENDPOINT }/projectsettings/`,
    ageGroups: `${ this.API_ENDPOINT }/agegroups/`
  }
  // ToDo: functions with generalized HTTP calls in here
}
