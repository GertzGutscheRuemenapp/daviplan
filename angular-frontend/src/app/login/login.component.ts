import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from "@angular/forms";
import { LOGIN_QUERY } from './graphql';
import { Apollo } from "apollo-angular";
import { AuthService } from '../auth.service';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})

export class LoginComponent implements OnInit {
  loginForm: FormGroup;

  constructor(private apollo: Apollo, private formBuilder: FormBuilder, private auth: AuthService,
              private translate: TranslateService) {
    this.loginForm = this.formBuilder.group({
      userName: '',
      password: ''
    });
  }

  onSubmit() {
    let pass = this.loginForm.value.password;
    let username = this.loginForm.value.userName;
    if (username && pass)
      this.auth.login({
        password: pass,
        username: username
      }).subscribe(()=>{}, (error) => {
        this.loginForm.setErrors({ 'error': this.translate.instant('Keine Übereinstimmung von Nutzer und Passwort') })
      });
  }

  ngOnInit(): void {
  }

}
