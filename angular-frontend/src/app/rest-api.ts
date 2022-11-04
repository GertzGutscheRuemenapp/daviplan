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
    fieldTypes: `${ this.API_ENDPOINT }/fieldtypes/`,
    infrastructures: `${ this.API_ENDPOINT }/infrastructures/`,
    places: `${ this.API_ENDPOINT }/places/`,
    capacities: `${ this.API_ENDPOINT }/capacities/`,
    services: `${ this.API_ENDPOINT }/services/`,
    demandRateSets: `${ this.API_ENDPOINT }/demandratesets/`,
    arealevels: `${ this.API_ENDPOINT }/arealevels/`,
    populations: `${ this.API_ENDPOINT }/populations/`,
    popEntries: `${ this.API_ENDPOINT }/populationentries/`,
    areaPopulation: `${ this.API_ENDPOINT }/indicators/aggregate_population/`,
    populationData: `${ this.API_ENDPOINT }/indicators/population_details/`,
    reachabilityPlace: `${ this.API_ENDPOINT }/indicators/reachability_place/`,
    reachabilityCell: `${ this.API_ENDPOINT }/indicators/reachability_cell/`,
    reachabilityNextPlace: `${ this.API_ENDPOINT }/indicators/reachability_next_place/`,
    areaDemand: `${ this.API_ENDPOINT }/indicators/demand/`,
    statistics: `${ this.API_ENDPOINT }/popstatistics/`,
    statisticsData: `${ this.API_ENDPOINT }/popstatentries/`,
    prognoses: `${ this.API_ENDPOINT }/prognoses/`,
    areas: `${ this.API_ENDPOINT }/areas/`,
    genders: `${ this.API_ENDPOINT }/genders/`,
    years: `${ this.API_ENDPOINT }/years/`,
    layerGroups: `${ this.API_ENDPOINT }/layergroups/`,
    layers: `${ this.API_ENDPOINT }/wmslayers/`,
    getCapabilities: `${ this.API_ENDPOINT }/wmslayers/getcapabilities/`,
    processes: `${ this.API_ENDPOINT }/planningprocesses/`,
    scenarios: `${ this.API_ENDPOINT }/scenarios/`,
    matrixCellPlaces: `${ this.API_ENDPOINT }/matrixcellplaces/`,
    transitMatrix: `${ this.API_ENDPOINT }/matrixstopstops/`,
    transitStops: `${ this.API_ENDPOINT }/stops/`,
    rasterCells: `${ this.API_ENDPOINT }/rastercells/`,
    closestCell: `${ this.API_ENDPOINT }/rastercells/closest_cell/`,
    modevariants: `${ this.API_ENDPOINT }/modevariants/`,
    networks: `${ this.API_ENDPOINT }/networks/`,
    routingStatistics: `${ this.API_ENDPOINT }/matrixstatistics/`,
    logs: `${ this.API_ENDPOINT }/logs/`
  }
  // ToDo: functions with generalized HTTP calls in here
}
