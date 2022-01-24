import { Injectable } from "@angular/core";
import {BehaviorSubject, Observable, of, Subject} from "rxjs";
import { RestAPI } from "./rest-api";
import { HttpClient } from "@angular/common/http";
import { Title } from "@angular/platform-browser";
import { ProjectSettings } from "./pages/administration/project-definition/project-definition.component";
import { AuthService } from "./auth.service";

export interface SiteSettings {
  id: number,
  title: string,
  contactMail: string,
  welcomeText: string,
  logo: string
}

@Injectable({ providedIn: 'root' })
export class SettingsService {
  siteSettings$ = new BehaviorSubject<SiteSettings>({
    id: 0, title: '', contactMail: '', welcomeText: '', logo: ''
  });
  projectSettings$ = new BehaviorSubject<ProjectSettings>({
    projectArea: '',
    startYear: 0,
    endYear: 0
  });
  userSettings$ = new BehaviorSubject<{}>({});

  constructor(private rest: RestAPI, private http: HttpClient, private titleService: Title, private authService: AuthService) {
    // initial fetch of settings
    this.fetchSiteSettings();
    this.fetchProjectSettings();
    this.fetchUserSettings();
  }

  fetchSiteSettings(): void {
    this.http.get<SiteSettings>(this.rest.URLS.settings)
      .subscribe(siteSettings => {  this.siteSettings$.next(siteSettings); });
  }

  fetchProjectSettings(): void {
    this.http.get<ProjectSettings>(this.rest.URLS.projectSettings)
      .subscribe(projectSettings => {  this.projectSettings$.next(projectSettings); });
  }

  fetchUserSettings(): void {
    this.authService.getCurrentUser().subscribe(
      user => this.userSettings$.next(user?.profile?.settings || {}))
  }

  applySettings(settings: SiteSettings) {
    this.titleService.setTitle(settings.title);
  }
}
