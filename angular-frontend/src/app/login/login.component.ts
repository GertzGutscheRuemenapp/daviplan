import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from "@angular/forms";
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})

export class LoginComponent implements OnInit {
  loginForm: FormGroup;

  constructor(private formBuilder: FormBuilder, private auth: AuthService) {
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
            this.loginForm.setErrors({ 'error': $localize`Keine Übereinstimmung von Nutzer und Passwort` })
          });
  }

  ngOnInit(): void {
  }

}
