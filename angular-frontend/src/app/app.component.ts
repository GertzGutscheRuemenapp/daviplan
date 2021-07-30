import { Component } from '@angular/core';
import { SettingsService } from "./settings.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {

  constructor(private settings: SettingsService) {
    // auto apply settings when new ones were fetched
    // ToDo: is this the right place for this?
    settings.siteSettings$.subscribe(settings => {
      this.settings.applySettings(settings);
    })
  }
}
