import { Injectable } from "@angular/core";
import {BehaviorSubject, Observable, of, Subject} from "rxjs";
import { RestAPI } from "./rest-api";
import { HttpClient } from "@angular/common/http";
import { pluck, share, shareReplay, tap, last } from 'rxjs/operators';

export interface SiteSettings {
  title: string,
  contactMail: string,
  logo: string,
  primaryColor: string,
  secondaryColor: string,
  welcomeText: string
}

@Injectable({ providedIn: 'root' })
export class SettingsService {
  siteSettings$ = new BehaviorSubject<SiteSettings>(null as any);

  constructor(private rest: RestAPI, private http: HttpClient ) {
    this.fetchSiteSettings();
  }

  fetchSiteSettings(): void {
    this.http.get<SiteSettings>(this.rest.URLS.settings)
      .subscribe(siteSettings => {  this.siteSettings$.next(siteSettings); });
  }
}
