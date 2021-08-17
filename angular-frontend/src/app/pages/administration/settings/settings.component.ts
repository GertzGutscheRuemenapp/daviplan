import { Component, AfterViewInit, ViewChild, ChangeDetectorRef, Input, TemplateRef, ElementRef } from '@angular/core';
import { SettingsService, SiteSettings } from "../../../settings.service";
import { InputCardComponent } from "../../../dash/input-card.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { FormBuilder, FormGroup } from "@angular/forms";
import { FileValidator } from 'ngx-material-file-input';
import { MatDialog } from "@angular/material/dialog";
import '@ckeditor/ckeditor5-build-classic/build/translations/de';
import * as ClassicEditor from '@ckeditor/ckeditor5-build-classic';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements AfterViewInit {
  @ViewChild('titleEdit') titleEdit!: InputCardComponent;
  @ViewChild('titleTemplate') titleTemplate!: TemplateRef<any>;
  @ViewChild('titleEditButton') titleEditButton!: HTMLElement;
  @ViewChild('contactEdit') contactEdit!: InputCardComponent;
  @ViewChild('contactTemplate') contactTemplate!: TemplateRef<any>;
  @ViewChild('contactEditButton') contactEditButton!: HTMLElement;
  @ViewChild('welcomeTextEdit') welcomeTextEdit!: InputCardComponent;
  @ViewChild('welcomeTextTemplate') welcomeTextTemplate!: TemplateRef<any>;
  @ViewChild('welcomeTextEditButton') welcomeTextEditButton!: HTMLElement;
  settings?: SiteSettings;
  titleForm!: FormGroup;
  contactForm!: FormGroup;
  logoForm!: FormGroup;
  welcomeTextInput: string = '';
  welcomeTextErrors: any = {};
  // 10MB (=10 * 2 ** 20)
  readonly maxLogoSize = 10485760;
  // workaround to have access to object iteration in template
  Object = Object;
  Editor = ClassicEditor;
  editorConfig = {
    toolbar: {
      items: ['heading', '|', 'bold', 'italic', '|', 'undo', 'redo', '-', 'numberedList', 'bulletedList']
    },
    language: 'de'
  };

  constructor(private settingsService: SettingsService, private http: HttpClient, private rest: RestAPI,
              private cdRef: ChangeDetectorRef, private formBuilder: FormBuilder, public dialog: MatDialog) {  }

  ngAfterViewInit(): void {
    this.settingsService.siteSettings$.subscribe(settings => {
      this.settings = Object.assign({}, settings);
      this.cdRef.detectChanges();
      this.welcomeTextInput = settings.welcomeText;
    });
    this.setupTitleDialog();
    this.setupContactDialog();
    this.setupWelcomeTextDialog();
  }

  setupTitleDialog(): void {
    this.titleForm = this.formBuilder.group({
      title: this.settings!.title
    });

    this.titleEdit.dialogConfirmed.subscribe(()=>{
      this.titleForm.setErrors(null);
      this.titleForm.markAllAsTouched();
      if (this.titleForm.invalid) return;
      this.titleEdit.setLoading(true);
      let attributes: any = { title: this.titleForm.value.title }
      this.titleEdit.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.settings, attributes
        ).subscribe(data => {
          this.titleEdit.closeDialog(true);
          // update global settings
          this.settingsService.fetchSiteSettings();
        },(error) => {
          // ToDo: set specific errors to fields
          this.titleForm.setErrors(error.error);
          this.titleEdit.setLoading(false);
      });
    })
    this.titleEdit.dialogClosed.subscribe((ok)=>{
      // reset form on cancel
      if (!ok){
        this.titleForm.reset({
          title: this.settings?.title,
        });
      }
    })
  }

  setupContactDialog(): void {
    this.contactForm = this.formBuilder.group({
      contact: this.settings!.contactMail
    });

    this.contactEdit.dialogConfirmed.subscribe(()=>{
      this.contactForm.setErrors(null);
      this.contactForm.markAllAsTouched();
      if (this.contactForm.invalid) return;
      this.contactEdit.setLoading(true);
      let attributes: any = { contactMail: this.contactForm.value.contact }
      this.contactEdit.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.settings, attributes
      ).subscribe(data => {
        this.contactEdit.closeDialog(true);
        // update global settings
        this.settingsService.fetchSiteSettings();
      },(error) => {
        // ToDo: set specific errors to fields
        if (error.error.contactMail)
          this.contactForm.controls['contact'].setErrors(error.error.contactMail)
        else
          this.contactForm.setErrors(error.error);
        this.contactEdit.setLoading(false);
      });
    })
    this.contactEdit.dialogClosed.subscribe((ok)=>{
      // reset form on cancel
      if (!ok){
        this.contactForm.reset({
          contact: this.settings!.contactMail
        });
      }
    })
  }

  setupWelcomeTextDialog() {
    this.welcomeTextEdit.dialogConfirmed.subscribe((ok)=>{
      let attributes: any = {
        welcomeText: this.welcomeTextInput
      }
      this.welcomeTextEdit.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.settings, attributes
      ).subscribe(settings => {
        // update global settings
        this.settingsService.fetchSiteSettings();
        this.welcomeTextEdit.closeDialog(true);
      },(error) => {
        this.welcomeTextErrors = error.error;
        this.welcomeTextEdit.setLoading(false);
      });
    });
    this.welcomeTextEdit.dialogClosed.subscribe((ok)=>{
      this.welcomeTextErrors = {};
      this.welcomeTextInput = this.settings!.welcomeText;
    });
  }


  //
  // setupTitleCard(): void {
  //   if (!this.settings || !this.titleCard) return;
  //   this.titleCard.dialogConfirmed.subscribe((ok)=>{
  //     this.titleForm.setErrors(null);
  //     // display errors for all fields even if not touched
  //     this.titleForm.markAllAsTouched();
  //     if (this.titleForm.invalid) return;
  //     let attributes: any = {
  //       title: this.titleForm.value.title,
  //       contactMail: this.titleForm.value.contact
  //     }
  //     this.titleCard?.setLoading(true);
  //     this.http.patch<SiteSettings>(this.rest.URLS.settings, attributes
  //     ).subscribe(data => {
  //       this.titleCard?.closeDialog(true);
  //       // update global settings
  //       this.settingsService.fetchSiteSettings();
  //     },(error) => {
  //       // ToDo: set specific errors to fields
  //       this.titleForm.setErrors(error.error);
  //       this.titleCard?.setLoading(false);
  //     });
  //   })
  //   this.titleCard.dialogClosed.subscribe((ok)=>{
  //     // reset form on cancel
  //     if (!ok){
  //       this.titleForm.reset({
  //         title: this.settings?.title,
  //         contact: this.settings?.contactMail,
  //       });
  //     }
  //   })
  // }
  //
  // setupWelcomeTextCard(): void {
  //   if (!this.settings || !this.welcomeTextCard) return;
  //   this.welcomeTextCard.dialogConfirmed.subscribe((ok)=>{
  //     let attributes: any = {
  //       welcomeText: this.welcomeTextInput
  //     }
  //     this.welcomeTextCard?.setLoading(true);
  //     this.http.patch<SiteSettings>(this.rest.URLS.settings, attributes
  //     ).subscribe(settings => {
  //       // update global settings
  //       this.settingsService.fetchSiteSettings();
  //       this.welcomeTextCard?.closeDialog(true);
  //     },(error) => {
  //       this.welcomeTextErrors = error.error;
  //       this.welcomeTextCard?.setLoading(false);
  //     });
  //   });
  //   this.welcomeTextCard.dialogClosed.subscribe((ok)=>{
  //     this.welcomeTextErrors = {};
  //   });
  // }

}
