import { Component } from '@angular/core';
import { AuthService } from "./auth.service";
import { SettingsService, SiteSettings } from "./settings.service";
import { Router } from "@angular/router";
import { Title } from "@angular/platform-browser";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {

  constructor(private settings: SettingsService, private titleService: Title) {
    settings.siteSettings$.subscribe(settings => {
      if (settings)
        this.applySettings(settings);
    })
  }

  applySettings(settings: SiteSettings) {
    this.titleService.setTitle(settings.title);
  }
}
