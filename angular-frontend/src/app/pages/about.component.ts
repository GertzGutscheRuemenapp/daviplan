import { Component, OnInit } from "@angular/core";
import { environment } from "../../environments/environment";
import { SettingsService } from "../settings.service";

@Component({
  templateUrl: './about.component.html',
  styleUrls: ['./welcome.component.scss', './about.component.scss']
})
export class AboutComponent implements OnInit {
  backend: string = environment.backend;
  version: string = '';

  constructor(private settingsService: SettingsService) {}

  ngOnInit(): void {
    this.settingsService.siteSettings$.subscribe(settings => {
      this.version = settings.version;
    });
  }
}
