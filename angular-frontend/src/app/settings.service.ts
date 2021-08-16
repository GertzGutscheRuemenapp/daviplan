import { Injectable } from "@angular/core";
import {BehaviorSubject, Observable, of, Subject} from "rxjs";
import { RestAPI } from "./rest-api";
import { HttpClient } from "@angular/common/http";
import { Title } from "@angular/platform-browser";

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

  constructor(private rest: RestAPI, private http: HttpClient, private titleService: Title) {
    // initial fetch of settings
    this.fetchSiteSettings();
  }

  fetchSiteSettings(): void {
    this.http.get<SiteSettings>(this.rest.URLS.settings)
      .subscribe(siteSettings => {  this.siteSettings$.next(siteSettings); });
  }

  applySettings(settings: SiteSettings) {
    this.titleService.setTitle(settings.title);
  }
}
