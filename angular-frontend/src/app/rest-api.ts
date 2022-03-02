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
    userSettings: `${ this.API_ENDPOINT }/users/current/usersettings/`,
    siteSettings: `${ this.API_ENDPOINT }/sitesettings/`,
    projectSettings: `${ this.API_ENDPOINT }/projectsettings/`,
    basedataSettings: `${ this.API_ENDPOINT }/basedatasettings/`,
    ageGroups: `${ this.API_ENDPOINT }/agegroups/`,
    infrastructures: `${ this.API_ENDPOINT }/infrastructures/`,
    places: `${ this.API_ENDPOINT }/places/`,
    capacities: `${ this.API_ENDPOINT }/capacities/`,
    services: `${ this.API_ENDPOINT }/services/`,
    arealevels: `${ this.API_ENDPOINT }/arealevels/`,
    areaPopulation: `${ this.API_ENDPOINT }/areaindicators/aggregate_population/`,
    populationData: `${ this.API_ENDPOINT }/populationindicators/population_details/`,
    areas: `${ this.API_ENDPOINT }/areas/`,
    genders: `${ this.API_ENDPOINT }/genders/`,
    years: `${ this.API_ENDPOINT }/years/`,
    layerGroups: `${ this.API_ENDPOINT }/layergroups/`,
    layers: `${ this.API_ENDPOINT }/wmslayers/`,
    getCapabilities: `${ this.API_ENDPOINT }/wmslayers/getcapabilities/`,
    processes: `${ this.API_ENDPOINT }/planningprocesses/`,
    scenarios: `${ this.API_ENDPOINT }/scenarios/`,
  }
  // ToDo: functions with generalized HTTP calls in here
}
