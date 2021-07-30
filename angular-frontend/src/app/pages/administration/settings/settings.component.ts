import { Component, AfterViewInit, ViewChild, ChangeDetectorRef } from '@angular/core';
import { SettingsService, SiteSettings } from "../../../settings.service";
import { DataCardComponent } from "../../../dash/data-card.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { AngularEditorConfig } from '@kolkov/angular-editor';
import { set } from "ol/transform";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { User } from "../../login/users";

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements AfterViewInit {
  @ViewChild('appearanceCard') appearanceCard?: DataCardComponent;
  @ViewChild('welcomeTextCard') welcomeTextCard?: DataCardComponent;
  @ViewChild('titleCard') titleCard?: DataCardComponent;
  settings?: SiteSettings;
  titleForm!: FormGroup;
  primaryColorInput: string = '';
  secondaryColorInput: string = '';
  welcomeTextInput: string = '';
  appearanceErrors: any = {};
  welcomeTextErrors: any = {};
  editorConfig: AngularEditorConfig = {
    editable: true,
    spellcheck: false,
    height: '300px',
    minHeight: '100px'
  }
  // workaround to have access to object iteration in template
  Object = Object;

  constructor(private settingsService: SettingsService, private http: HttpClient, private rest: RestAPI,
              private cdRef:ChangeDetectorRef, private formBuilder: FormBuilder) {  }

  ngAfterViewInit(): void {
    this.settingsService.siteSettings$.subscribe(settings => {
      this.settings = Object.assign({}, settings);
      this.cdRef.detectChanges();
      this.setupTitleCard();
      this.setupAppearanceCard();
      this.setupWelcomeTextCard();
    });
  }

  setupTitleCard(): void {
    if (!this.settings || !this.titleCard) return;
    this.titleForm = this.formBuilder.group({
      title: this.settings.title,
      contact: this.settings.contactMail
    });
    this.titleCard.dialogConfirmed.subscribe((ok)=>{
      this.titleForm.setErrors(null);
      // display errors for all fields even if not touched
      this.titleForm.markAllAsTouched();
      if (this.titleForm.invalid) return;
      let attributes: any = {
        title: this.titleForm.value.title,
        contactMail: this.titleForm.value.contact
      }
      this.titleCard?.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.settings, attributes
      ).subscribe(data => {
        this.titleCard?.closeDialog(true);
        // update global settings
        this.settingsService.fetchSiteSettings();
      },(error) => {
        // ToDo: set specific errors to fields
        this.titleForm.setErrors(error.error);
        this.titleCard?.setLoading(false);
      });
    })
    this.titleCard.dialogClosed.subscribe((ok)=>{
      // reset form on cancel
      if (!ok){
        this.titleForm.reset({
          title: this.settings?.title,
          contact: this.settings?.contactMail,
        });
      }
    })
  }

  setupAppearanceCard(): void {
    if (!this.settings || !this.appearanceCard) return;
    this.primaryColorInput = this.settings.primaryColor;
    this.secondaryColorInput = this.settings.secondaryColor;
    this.appearanceCard.dialogConfirmed.subscribe((ok)=>{
      let attributes: any = {
        primaryColor: this.primaryColorInput,
        secondaryColor: this.secondaryColorInput
      }
      this.appearanceCard?.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.settings, attributes
      ).subscribe(settings => {
        this.appearanceCard?.closeDialog(true);
        // update global settings
        this.settingsService.fetchSiteSettings();
      },(error) => {
        this.appearanceErrors = error.error;
        this.appearanceCard?.setLoading(false);
      });
    });
    this.appearanceCard.dialogClosed.subscribe((ok)=>{
      // reset colors on cancel
      if (!ok){
        this.primaryColorInput = this.settings!.primaryColor;
        this.secondaryColorInput = this.settings!.secondaryColor;
        this.settingsService.setColor({ primary: this.primaryColorInput, secondary: this.secondaryColorInput });
      }
      this.appearanceErrors = {};
    });
  }

  onPrimaryChange(hex: string): void {
    this.settingsService.setColor({ primary: this.primaryColorInput });
  }

  onSecondaryChange(hex: string): void {
    this.settingsService.setColor({ secondary: this.secondaryColorInput });
  }

  setupWelcomeTextCard(): void {
    if (!this.settings || !this.welcomeTextCard) return;
    this.welcomeTextInput = this.settings.welcomeText;
    this.welcomeTextCard.dialogConfirmed.subscribe((ok)=>{
      let attributes: any = {
        welcomeText: this.welcomeTextInput
      }
      this.welcomeTextCard?.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.settings, attributes
      ).subscribe(settings => {
        // update global settings
        this.settingsService.fetchSiteSettings();
        this.welcomeTextCard?.closeDialog(true);
      },(error) => {
        this.welcomeTextErrors = error.error;
        this.welcomeTextCard?.setLoading(false);
      });
    });
    this.welcomeTextCard.dialogClosed.subscribe((ok)=>{
      this.welcomeTextErrors = {};
      this.settingsService.setColor({ primary: this.primaryColorInput, secondary: this.secondaryColorInput });
    });
  }

}
