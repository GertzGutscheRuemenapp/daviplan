import { Component, AfterViewInit, ViewChild, ChangeDetectorRef } from '@angular/core';
import { SettingsService, SiteSettings } from "../../../settings.service";
import { DataCardComponent } from "../../../dash/data-card.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements AfterViewInit {
  @ViewChild('appearanceCard') appearanceCard?: DataCardComponent;
  settings?: SiteSettings;
  primaryColor: string = '';
  secondaryColor: string = '';
  appearanceErrors: any = {};
  // workaround to have access to object iteration in template
  Object = Object;

  constructor(private settingsService: SettingsService, private http: HttpClient, private rest: RestAPI,
              private cdRef:ChangeDetectorRef) {  }

  ngAfterViewInit(): void {
    this.settingsService.siteSettings$.subscribe(settings => {
      this.settings = settings;
      this.cdRef.detectChanges();
      this.setupAppearanceCard();
    });
  }

  setupAppearanceCard(): void {
    if (!this.settings || !this.appearanceCard) return;
    this.primaryColor = this.settings.primaryColor;
    this.secondaryColor = this.settings.secondaryColor;
    this.appearanceCard.dialogConfirmed.subscribe((ok)=>{
      let attributes: any = {
        id: this.settings?.id,
        primaryColor: this.primaryColor,
        secondaryColor: this.secondaryColor
      }
      this.appearanceCard?.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.settings, attributes
      ).subscribe(settings => {
        this.appearanceCard?.closeDialog();
      },(error) => {
        this.appearanceErrors = error.error;
        this.appearanceCard?.setLoading(false);
      });
    });
    this.appearanceCard.dialogClosed.subscribe((ok)=>{
      // reset colors on cancel
      if (!ok){
        this.primaryColor = this.settings!.primaryColor;
        this.secondaryColor = this.settings!.secondaryColor;
        this.appearanceErrors = {};
      }
    });
  }

  onPrimaryChange(hex: string): void {
    this.settingsService.setColor({ primary: this.primaryColor });
  }

  onSecondaryChange(hex: string): void {
    this.settingsService.setColor({ secondary: this.secondaryColor });
  }

}
