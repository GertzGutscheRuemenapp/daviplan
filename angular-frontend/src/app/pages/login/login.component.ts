import { Component } from '@angular/core';
import { FormBuilder, FormGroup } from "@angular/forms";
import { AuthService } from '../../auth.service';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { Router } from "@angular/router";
import { SettingsService, SiteSettings } from "../../settings.service";
import { environment } from "../../../environments/environment";
import { User } from "../../rest-interfaces";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})

export class LoginComponent {
  settings?: SiteSettings;
  loginForm: FormGroup;
  user?: User;
  showPassword: boolean = false;
  faEye = faEye;
  faEyeSlash = faEyeSlash;
  backend: string = environment.backend;

  constructor(private settingsService: SettingsService, private formBuilder: FormBuilder, public auth: AuthService,
              private router: Router) {
    this.settingsService.siteSettings$.subscribe(settings => {
      this.settings = settings;
    });
    this.loginForm = this.formBuilder.group({
      userName: '',
      password: ''
    });
    auth.getCurrentUser().subscribe(user=>this.user=user)
  }

  onSubmit() {
    let pass = this.loginForm.value.password;
    let username = this.loginForm.value.userName;
    if (username && pass)
       this.auth.login({
            password: pass,
            username: username
          }).subscribe(token => {
            // fetch global settings after logged in
            this.settingsService.refresh();
            this.router.navigate(['/']);
          }, (error) => {
            const msg = (error.status === 0) ? 'Server antwortet nicht': $localize`Keine Übereinstimmung von Nutzer und Passwort`;
            this.loginForm.setErrors({ 'error': msg })
          });
  }
}
