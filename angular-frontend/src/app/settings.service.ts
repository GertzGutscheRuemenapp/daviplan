import { Injectable } from "@angular/core";
import {BehaviorSubject, Observable, of, Subject} from "rxjs";
import { RestAPI } from "./rest-api";
import { HttpClient } from "@angular/common/http";
import { pluck, share, shareReplay, tap, last } from 'rxjs/operators';
import { Title } from "@angular/platform-browser";
import { MaterialCssVarsService } from "angular-material-css-vars";

export interface SiteSettings {
  id: number,
  title: string,
  contactMail: string,
  logo: string,
  primaryColor: string,
  secondaryColor: string,
  welcomeText: string
}

@Injectable({ providedIn: 'root' })
export class SettingsService {
  siteSettings$ = new BehaviorSubject<SiteSettings>({
    id: 0, title: '', contactMail: '', logo: '', primaryColor: '', secondaryColor: '', welcomeText: ''
  });

  constructor(private rest: RestAPI, private http: HttpClient, private titleService: Title,
              public materialCssVarsService: MaterialCssVarsService ) {
    // initial fetch of settings
    this.fetchSiteSettings();
  }

  fetchSiteSettings(): void {
    this.http.get<SiteSettings>(this.rest.URLS.settings)
      .subscribe(siteSettings => {  this.siteSettings$.next(siteSettings); });
  }

  applySettings(settings: SiteSettings) {
    this.titleService.setTitle(settings.title);
    this.setColor({ primary: settings.primaryColor, secondary: settings.secondaryColor, warn: 'red' });
  }

  setColor(colors: {primary?: string, secondary?: string, warn?: string}) {
    if (colors.primary) this.materialCssVarsService.setPrimaryColor(colors.primary);
    if (colors.secondary) this.materialCssVarsService.setAccentColor(colors.secondary);
    if (colors.warn) this.materialCssVarsService.setWarnColor(colors.warn);
  }
}
