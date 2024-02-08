import { Component, AfterViewInit, ViewChild, ChangeDetectorRef } from '@angular/core';
import { SettingsService, SiteSettings } from "../../../settings.service";
import { InputCardComponent } from "../../../dash/input-card.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { FormBuilder, FormGroup } from "@angular/forms";
import { MatDialog } from "@angular/material/dialog";
import '@ckeditor/ckeditor5-build-classic/build/translations/de';
import * as ClassicEditor from '@ckeditor/ckeditor5-build-classic';
import { FileHandle } from "../../../helpers/dragndrop.directive";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { take } from "rxjs/operators";
import { showAPIError } from "../../../helpers/utils";
import { environment } from "../../../../environments/environment";

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements AfterViewInit {
  @ViewChild('titleEdit') titleEdit!: InputCardComponent;
  @ViewChild('contactEdit') contactEdit!: InputCardComponent;
  @ViewChild('welcomeTextEdit') welcomeTextEdit!: InputCardComponent;
  @ViewChild('logoEdit') logoEdit!: InputCardComponent;
  @ViewChild('regstatEdit') regstatEdit!: InputCardComponent;
  @ViewChild('BKGEdit') BKGEdit!: InputCardComponent;
  faEye = faEye;
  faEyeSlash = faEyeSlash;
  settings?: SiteSettings;
  titleForm!: FormGroup;
  contactForm!: FormGroup;
  regstatForm!: FormGroup;
  BKGForm!: FormGroup;
  showBKGPassword: boolean = false;
  showRegstatPassword: boolean = false;
  welcomeTextInput: string = '';
  // 10MB (=10 * 2 ** 20)
  readonly maxLogoSize = 10485760;
  Editor = ClassicEditor;
  logoFile?: FileHandle;
  editorConfig = {
    toolbar: {
      items: ['heading', '|', 'bold', 'italic', '|', 'undo', 'redo', '-', 'numberedList', 'bulletedList']
    },
    language: 'de'
  };
  backend: string = environment.backend;

  constructor(private settingsService: SettingsService, private http: HttpClient, private rest: RestAPI,
              private cdRef: ChangeDetectorRef, private formBuilder: FormBuilder, public dialog: MatDialog) {  }

  ngAfterViewInit(): void {
    this.settingsService.siteSettings$.pipe(take(1)).subscribe(settings => {
      this.settings = Object.assign({}, settings);
      this.cdRef.detectChanges();
      this.welcomeTextInput = settings.welcomeText;
      this.setupTitleDialog();
      this.setupContactDialog();
      this.setupWelcomeTextDialog();
      this.setupLogoDialog();
    });
    this.setupRegstatDialog();
    this.setupBKGDialog();
  }

  setupTitleDialog(): void {
    this.titleForm = this.formBuilder.group({
      title: this.settings!.title
    });

    this.titleEdit.dialogConfirmed.subscribe(()=>{
      this.titleForm.markAllAsTouched();
      if (this.titleForm.invalid) return;
      this.titleEdit.setLoading(true);
      let attributes: any = { title: this.titleForm.value.title }
      this.titleEdit.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.siteSettings, attributes
        ).subscribe(settings => {
          this.settings = Object.assign({}, settings);
          this.titleEdit.closeDialog(true);
          // update global settings
          this.settingsService.refresh().subscribe();
        },(error) => {
          showAPIError(error, this.dialog);
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
      this.contactForm.markAllAsTouched();
      if (this.contactForm.invalid) return;
      this.contactEdit.setLoading(true);
      let attributes: any = { contactMail: this.contactForm.value.contact }
      this.contactEdit.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.siteSettings, attributes
      ).subscribe(settings => {
        this.settings = Object.assign({}, settings);
        this.contactEdit.closeDialog(true);
        // update global settings
        this.settingsService.refresh().subscribe();
      },(error) => {
        showAPIError(error, this.dialog);
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
      this.http.patch<SiteSettings>(this.rest.URLS.siteSettings, attributes
      ).subscribe(settings => {
        this.settings = Object.assign({}, settings);
        // update global settings
        this.settingsService.refresh().subscribe();
        this.welcomeTextEdit.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.welcomeTextEdit.setLoading(false);
      });
    });
    this.welcomeTextEdit.dialogClosed.subscribe((ok)=>{
      this.welcomeTextInput = this.settings!.welcomeText;
    });
  }

  setupLogoDialog() {
    this.logoEdit.dialogConfirmed.subscribe((ok)=>{
      const formData = new FormData();
      if (!this.logoFile) {
        showAPIError({message: 'Die Datei darf nicht leer sein.'}, this.dialog);
        return;
      }
      formData.append('logo', this.logoFile.file);
      this.logoEdit?.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.siteSettings, formData
      ).subscribe(settings => {
        this.settings = Object.assign({}, settings);
        this.logoEdit?.closeDialog(true);
        // update global settings
        this.settingsService.refresh().subscribe();
      },(error) => {
        showAPIError(error, this.dialog);
        this.logoEdit?.setLoading(false);
      });
    });
    this.logoEdit.dialogClosed.subscribe((ok)=> {
      this.logoFile = undefined;
    })
  }

  filesDropped(files: FileHandle[]): void {
    // ToDo: verify file
    this.logoFile = files[0];
  }

  removeLogo(): void {
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Soll das Logo entfernt werden?`,
        confirmButtonText: $localize`Logo entfernen`,
        value: this.logoFileName()
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.patch<SiteSettings>(this.rest.URLS.siteSettings, { logo: null }
        ).subscribe( settings => {
          this.settings = Object.assign({}, settings);
          this.settingsService.refresh().subscribe();
        } )
      }
    });
  }

  logoFileName(): string | undefined {
    if (!this.settings?.logo) return;
    let split = this.settings?.logo.split('/');
    return split[split.length - 1];
  }

  setupRegstatDialog(): void {
    this.regstatForm = this.formBuilder.group({
      regstatUser: this.settings!.regionalstatistikUser,
      regstatPassword: ''
    });
    this.regstatEdit.dialogConfirmed.subscribe(()=>{
      this.regstatForm.markAllAsTouched();
      if (this.regstatForm.invalid) return;
      let attributes: any = {
        regionalstatistikUser: this.regstatForm.value.regstatUser,
        regionalstatistikPassword: this.regstatForm.value.regstatPassword
      }
      this.regstatEdit.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.siteSettings, attributes
      ).subscribe(settings => {
        this.regstatEdit.closeDialog(true);
        this.settings = Object.assign({}, settings);
        // update global settings
        this.settingsService.refresh().subscribe();
      },(error) => {
        showAPIError(error, this.dialog);
        this.regstatEdit.setLoading(false);
      });
    })
    this.regstatEdit.dialogClosed.subscribe((ok)=>{
      if (!ok){
        this.contactForm.reset({
          regstatUser: this.settings!.regionalstatistikUser,
          regstatPassword: ''
        });
      }
    })
  }

  removeRegstatCredentials(): void {
    let attributes: any = {
      regionalstatistikUser: '',
      regionalstatistikPassword: ''
    }
    this.http.patch<SiteSettings>(this.rest.URLS.siteSettings, attributes
    ).subscribe(settings => {
      this.settings = Object.assign({}, settings);
      // update global settings
      this.settingsService.refresh().subscribe();
    },(error) => {
      showAPIError(error, this.dialog);
    });
  }

  setupBKGDialog(): void {
    this.BKGForm = this.formBuilder.group({
      bkgPassword: ''
    });
    this.BKGEdit.dialogConfirmed.subscribe(()=>{
      this.BKGForm.setErrors(null);
      this.BKGForm.markAllAsTouched();
      if (this.BKGForm.invalid) return;
      let attributes: any = {
        bkgPassword: this.BKGForm.value.bkgPassword || '',
      }
      this.BKGEdit.setLoading(true);
      this.http.patch<SiteSettings>(this.rest.URLS.siteSettings, attributes
      ).subscribe(settings => {
        this.settings = Object.assign({}, settings);
        this.settingsService.refresh().subscribe();
        this.BKGEdit.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.BKGEdit.setLoading(false);
      });
    })
    this.BKGEdit.dialogClosed.subscribe((ok)=>{
      if (!ok){
        this.contactForm.reset({
          bkgPassword: ''
        });
      }
    })
  }

  removeBKGCredentials(): void {
    let attributes: any = {
      bkgPassword: '',
    }
    this.http.patch<SiteSettings>(this.rest.URLS.siteSettings, attributes
    ).subscribe(settings => {
      this.settings = Object.assign({}, settings);
      // update global settings
      this.settingsService.refresh().subscribe();
    },(error) => {
      showAPIError(error, this.dialog);
    });
  }
}
