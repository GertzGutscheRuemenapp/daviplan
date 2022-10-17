import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable } from "rxjs";
import { RestAPI } from "./rest-api";
import { HttpClient } from "@angular/common/http";
import { Title } from "@angular/platform-browser";
import { ProjectSettings } from "./pages/administration/project-definition/project-definition.component";
import { BasedataSettings } from "./rest-interfaces";
import { environment } from "../environments/environment";

export interface SiteSettings {
  id: number,
  title: string,
  contactMail: string,
  welcomeText: string,
  logo: string,
  regionalstatistikUser: string
}

class UserSettings {
  private settings$ = new BehaviorSubject<Record<string, any>>({});
  private _settings: Record<string, any> = {};

  constructor(private rest: RestAPI, private http: HttpClient) {
    this.fetch();
  }

  get(key: string): Observable<any>{
    const observable = new Observable<any>(subscriber => {
      this.settings$.subscribe(settings => {
        subscriber.next(settings[key]);
        subscriber.complete();
      });
    });
    return observable;
  }

  fetch(): void {
    this.http.get<{}>(this.rest.URLS.userSettings)
      .subscribe(userSettings => {
        this._settings = userSettings;
        this.settings$.next(userSettings);
      });
  }

  set(key: string, value: any, options: { patch: boolean } = { patch: true }): void {
    this._settings[key] = value;
    if (options.patch) {
      let patchData: Record<string, any> = {};
      patchData[key] = value;
      this.http.patch<{}>(this.rest.URLS.userSettings, patchData)
        .subscribe(userSettings => {  this.settings$.next(userSettings); });
    }
  }

  save(): void {
    this.http.post<{}>(this.rest.URLS.userSettings, this._settings)
      .subscribe(userSettings => {  this.settings$.next(userSettings); });
  }
}

@Injectable({ providedIn: 'root' })
export class SettingsService {
  siteSettings$ = new BehaviorSubject<SiteSettings>({
    id: 0, title: '', contactMail: '', welcomeText: '', logo: '', regionalstatistikUser: ''
  });
  baseDataSettings$ = new BehaviorSubject<BasedataSettings>({
    popStatisticsAreaLevel: 0,
    popAreaLevel: 0,
    defaultDemandRateSets: [],
    defaultModeVariants: [],
    defaultPrognosis: 0
  });
  projectSettings$ = new BehaviorSubject<ProjectSettings>({
    projectArea: '',
    startYear: 0,
    endYear: 0,
    minYear: 0
  });
  user!: UserSettings;

  constructor(private rest: RestAPI, private http: HttpClient, private titleService: Title) {
    this.refresh();
  }

  refresh(): void {
    this.fetchSiteSettings();
    this.fetchProjectSettings();
    this.fetchBaseDataSettings();
    this.user = new UserSettings(this.rest, this.http);
  }

  public fetchSiteSettings(): void {
    this.http.get<SiteSettings>(this.rest.URLS.siteSettings)
      .subscribe(siteSettings => {
        if (environment.production) {
          if (siteSettings.logo)
            siteSettings.logo = siteSettings.logo.replace('http:', 'https:');
        }
        this.siteSettings$.next(siteSettings)
      });
  }

  public fetchProjectSettings(): void {
    this.http.get<ProjectSettings>(this.rest.URLS.projectSettings)
      .subscribe(projectSettings => this.projectSettings$.next(projectSettings));
  }

  public fetchBaseDataSettings(): void {
    this.http.get<BasedataSettings>(this.rest.URLS.basedataSettings)
      .subscribe((basedataSettings) => this.baseDataSettings$.next(basedataSettings));
  }

  applySiteSettings(settings: SiteSettings) {
    this.titleService.setTitle(settings.title);
  }

}
