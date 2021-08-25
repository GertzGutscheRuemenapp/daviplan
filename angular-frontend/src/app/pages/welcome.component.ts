import { Component, OnInit } from '@angular/core';
import { SettingsService, SiteSettings } from "../settings.service";

@Component({
  selector: 'app-pages',
  templateUrl: './welcome.component.html',
  styleUrls: ['./welcome.component.scss']
})
export class WelcomeComponent implements OnInit {
  settings?: SiteSettings;

  constructor(private settingsService: SettingsService) {
    this.settingsService.siteSettings$.subscribe(settings => {
      this.settings = settings;
    });
  }

  ngOnInit(): void { }

}
