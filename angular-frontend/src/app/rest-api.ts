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
    settings: `${ this.API_ENDPOINT }/sitesettings/`,
    projectSettings: `${ this.API_ENDPOINT }/projectsettings/`,
    ageGroups: `${ this.API_ENDPOINT }/agegroups/`,
    infrastructures: `${ this.API_ENDPOINT }/infrastructures/`,
    layerGroups: `${ this.API_ENDPOINT }/layergroups/`,
    layers: `${ this.API_ENDPOINT }/wmslayers/`,
    internalLayers: `${ this.API_ENDPOINT }/internallayers/`,
    getCapabilities: `${ this.API_ENDPOINT }/wmslayers/getcapabilities/`
  }
  // ToDo: functions with generalized HTTP calls in here
}
