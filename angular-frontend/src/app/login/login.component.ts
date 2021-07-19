import { Component } from '@angular/core';
import { FormBuilder, FormGroup } from "@angular/forms";
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})

export class LoginComponent {
  loginForm: FormGroup;

  constructor(private formBuilder: FormBuilder, public auth: AuthService) {
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
          }).subscribe(user => {

       }, (error) => {
            this.loginForm.setErrors({ 'error': $localize`Keine Übereinstimmung von Nutzer und Passwort` })
          });
  }

}
