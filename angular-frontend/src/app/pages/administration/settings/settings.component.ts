import { Component, AfterViewInit, ViewChild, ChangeDetectorRef } from '@angular/core';
import { SettingsService, SiteSettings } from "../../../settings.service";
import { DataCardComponent } from "../../../dash/data-card.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { AngularEditorConfig } from '@kolkov/angular-editor';
import { FormBuilder, FormGroup } from "@angular/forms";

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements AfterViewInit {
  @ViewChild('welcomeTextCard') welcomeTextCard?: DataCardComponent;
  @ViewChild('titleCard') titleCard?: DataCardComponent;
  settings?: SiteSettings;
  titleForm!: FormGroup;
  welcomeTextInput: string = '';
  appearanceErrors: any = {};
  welcomeTextErrors: any = {};
  editorConfig: AngularEditorConfig = {
    editable: true,
    spellcheck: false,
    height: '300px',
    minHeight: '100px'
  }
  // 10MB (=10 * 2 ** 20)
  readonly maxLogoSize = 10485760;
  // workaround to have access to object iteration in template
  Object = Object;

  constructor(private settingsService: SettingsService, private http: HttpClient, private rest: RestAPI,
              private cdRef:ChangeDetectorRef, private formBuilder: FormBuilder) {  }

  ngAfterViewInit(): void {
    this.settingsService.siteSettings$.subscribe(settings => {
      this.settings = Object.assign({}, settings);
      this.cdRef.detectChanges();
      this.titleForm = this.formBuilder.group({
        title: this.settings.title,
        contact: this.settings.contactMail
      });
      this.welcomeTextInput = this.settings.welcomeText;
    });
    this.setupTitleCard();
    this.setupWelcomeTextCard();
  }

  setupTitleCard(): void {
    if (!this.settings || !this.titleCard) return;
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

  setupWelcomeTextCard(): void {
    if (!this.settings || !this.welcomeTextCard) return;
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
    });
  }

}
