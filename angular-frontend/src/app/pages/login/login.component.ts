import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from "@angular/forms";
import { AuthService } from '../../auth.service';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { ActivatedRoute, Router } from "@angular/router";
import { SettingsService, SiteSettings } from "../../settings.service";
import { environment } from "../../../environments/environment";
import { User } from "../../rest-interfaces";
import { Subscription } from "rxjs";
import { RestCacheService } from "../../rest-cache.service";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})

export class LoginComponent implements OnInit, OnDestroy {
  settings?: SiteSettings;
  loginForm: FormGroup;
  user?: User;
  showPassword: boolean = false;
  faEye = faEye;
  faEyeSlash = faEyeSlash;
  backend: string = environment.backend;
  next: string = '';
  private sub?: Subscription;

  constructor(private formBuilder: FormBuilder, public auth: AuthService,
              private router: Router, private route: ActivatedRoute,
              private rest: RestCacheService, private settingsService: SettingsService) {
    this.loginForm = this.formBuilder.group({
      userName: '',
      password: ''
    });
  }

  ngOnInit(): void {
    this.settingsService.siteSettings$.subscribe(settings => {
      this.settings = settings;
    });
    this.route.queryParams.subscribe(params => {
        this.next = params.next;
      }
    );
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
            this.settingsService.refresh().subscribe();
            // reset rest caches
            this.rest.reset();
            this.router.navigate([this.next || '/']);
          }, (error) => {
            const msg = (error.status === 0)? 'Server antwortet nicht': $localize`Keine Übereinstimmung von Nutzer und Passwort`;
            this.loginForm.setErrors({ 'error': msg })
          });
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }
}
