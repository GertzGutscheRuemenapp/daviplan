import { Component, OnInit } from '@angular/core';
import { SettingsService } from "../settings.service";

@Component({
  selector: 'app-pages',
  templateUrl: './welcome.component.html',
  styleUrls: ['./welcome.component.scss']
})
export class WelcomeComponent implements OnInit {
  welcomeText: string = '';

  constructor(private settingsService: SettingsService) {
    this.settingsService.siteSettings$.subscribe(settings => {
      this.welcomeText = settings.welcomeText;
    });
  }

  ngOnInit(): void { }

}
