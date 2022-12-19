import { AfterViewInit, Component, TemplateRef, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDialogComponent } from '../../../dialogs/confirm-dialog/confirm-dialog.component';
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { InputCardComponent } from '../../../dash/input-card.component'
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { RestAPI } from "../../../rest-api";
import { BehaviorSubject } from "rxjs";
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { Infrastructure, InfrastructureAccess, User } from "../../../rest-interfaces";
import { showAPIError } from "../../../helpers/utils";

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})

export class UsersComponent implements AfterViewInit  {

  @ViewChild('accountCard') accountCard?: InputCardComponent;
  @ViewChild('permissionCard') permissionCard?: InputCardComponent;
  @ViewChild('accessCard') accessCard?: InputCardComponent;
  @ViewChild('createUser') createUserTemplate?: TemplateRef<any>;
  faEye = faEye;
  faEyeSlash = faEyeSlash;
  accountForm!: FormGroup;
  permissionForm!: FormGroup;
  accessForm!: FormGroup;
  createUserForm: FormGroup;
  users: User[] = [];
  infrastructures: Infrastructure[] = [];
  selectedUser?: User;
  changePassword: boolean = false;
  showAccountPassword: boolean = false;
  showNewUserPassword: boolean = false;
  isLoading$ = new BehaviorSubject<boolean>(true);

  constructor(private http: HttpClient, private dialog: MatDialog, private formBuilder: FormBuilder,
              private rest: RestAPI) {
    this.createUserForm = this.formBuilder.group({
      username: new FormControl(''),
      password: new FormControl(''),
      confirmPass: new FormControl('')
    });
  }

  ngAfterViewInit() {
    this.http.get<Infrastructure[]>(this.rest.URLS.infrastructures).subscribe(infrastructures => {
      this.infrastructures = infrastructures;
      this.http.get<User[]>(this.rest.URLS.users).subscribe((users)=>{
        // sort users alphabetically, admins always on top
        this.users = users.slice().sort((a,b) =>
          (!a.isSuperuser && b.isSuperuser)? 1 : (a.isSuperuser && !b.isSuperuser)? -1 :
            (a.username > b.username)? 1 : (a.username < b.username)? -1 : 0);
        this.isLoading$.next(false);
      })
    })
    this.setupAccountCard();
    this.setupPermissionCard();
    this.setupAccessCard();
  }

  setupAccountCard(){
    if (!this.accountCard) return;
    this.accountCard.dialogConfirmed.subscribe((ok)=>{
      // display errors for all fields even if not touched
      this.accountForm.markAllAsTouched();
      if (this.accountForm.invalid) return;
      let user = this.accountForm.value.user;
      let attributes: any = {
          id: this.selectedUser?.id,
          username: user.username,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName
      }
      if (this.accountForm.value.changePass){
        let pass = this.accountForm.value.password
        if (pass != this.accountForm.value.confirmPass){
          showAPIError({message: 'Die Passwörter stimmen nicht überein'}, this.dialog);
          return;
        }
        attributes.password = pass;
      }
      this.accountCard?.setLoading(true);
      this.http.patch<User>(`${this.rest.URLS.users}${this.selectedUser?.id}/`, attributes
      ).subscribe(user => {
        this.selectedUser!.username = user.username;
        this.selectedUser!.email = user.email;
        this.selectedUser!.firstName = user.firstName;
        this.selectedUser!.lastName = user.lastName;
        this.accountCard?.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.accountCard?.setLoading(false);
      });
    })
    this.accountCard.dialogClosed.subscribe((ok)=>{
      this.changePassword = false;
      this.showAccountPassword = false;
      this.accountForm.controls['password'].disable();
      this.accountForm.controls['confirmPass'].disable();
      this.accountForm.reset({
        user: this.selectedUser,
        changePass: this.changePassword,
        password: '',
        confirmPass: ''
      });
    })
  }

  setupPermissionCard() {
    if (!this.permissionCard) return;
    this.permissionCard.dialogConfirmed.subscribe((ok)=>{
      let profile = this.permissionForm.value.profile;
      let attributes = {
        profile: {
          adminAccess: profile.adminAccess,
          canCreateProcess: profile.canCreateProcess,
          canEditBasedata: profile.canEditBasedata
        }
      }
      this.permissionCard?.setLoading(true);
      this.http.patch<User>(`${this.rest.URLS.users}${this.selectedUser?.id}/`, attributes
      ).subscribe(user => {
        this.selectedUser!.profile = user.profile;
        this.permissionCard?.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.permissionCard?.setLoading(false);
      });
    })
    this.permissionCard?.dialogClosed.subscribe((ok)=>{
      // reset form on cancel
      if (!ok){
        this.permissionForm.reset({
          user: this.selectedUser
        });
      }
    })
  }

  setupAccessCard() {
    if (!this.accessCard) return;
    this.accessCard.dialogOpened.subscribe(evt => {
      let accessControl: any = {};
      this.infrastructures.forEach(infrastructure => {
        const ua = this.userAccess(this.selectedUser, infrastructure);
        const access = {
          infrastructure: infrastructure,
          hasAccess: ua !== undefined,
          allowSensitiveData: ua?.allowSensitiveData || false
        }
        accessControl[infrastructure.id] = this.formBuilder.group(access);
      })
      this.accessForm = this.formBuilder.group(accessControl);
    })
    this.accessCard.dialogConfirmed.subscribe((ok)=>{
      this.accessCard?.setLoading(true);
      let access: any[] = [];
      Object.keys(this.accessForm.controls).forEach(infrastructureId => {
        const control = this.accessForm.value[infrastructureId];
        if (control.hasAccess) {
          access.push({
            infrastructure: infrastructureId,
            allowSensitiveData: control.allowSensitiveData
          })
        }
      })
      this.http.patch<User>(`${this.rest.URLS.users}${this.selectedUser?.id}/`, { access: access }
      ).subscribe(user => {
        this.selectedUser!.access = user.access;
        this.accessCard?.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.accessCard?.setLoading(false);
      });
    })
  }

  onSelect(user: User) {
    this.selectedUser = user;
    this.accountForm = this.formBuilder.group({
      user: this.formBuilder.group(this.selectedUser),
      changePass: this.changePassword,
      password: new FormControl({value: '', disabled: !this.changePassword}),
      confirmPass: new FormControl({value: '', disabled: !this.changePassword})
    });
    // let userControl: any = this.accountForm.get('user');
    // userControl.get('email').setValidators([Validators.email])
    this.permissionForm = this.formBuilder.group({
      profile: this.formBuilder.group(this.selectedUser.profile)
    });
  }

  onTogglePassChange(checked: boolean) {
    this.changePassword = checked;
    if (checked){
      this.accountForm.controls['password'].enable();
      this.accountForm.controls['confirmPass'].enable();
    }
    else {
      this.accountForm.controls['password'].disable();
      this.accountForm.controls['confirmPass'].disable();
    }
  }

  onCreateUser() {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Neuer Nutzer',
        template: this.createUserTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.afterClosed().subscribe((ok: boolean) => {
      this.createUserForm.reset();
      this.showNewUserPassword = false;
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.createUserForm.markAllAsTouched();
      if (this.createUserForm.invalid) return;
      let username = this.createUserForm.value.username;
      let password = this.createUserForm.value.password;
      if (password != this.createUserForm.value.confirmPass){
        showAPIError({message: 'Die Passwörter stimmen nicht überein'}, this.dialog);
        return;
      }
      dialogRef.componentInstance.isLoading$.next(true);
      let attributes = {
        username: username,
        password: password
      };
      this.http.post<User>(this.rest.URLS.users, attributes
      ).subscribe(user => {
        this.users.push(user);
        dialogRef.close();
      },(error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  onDeleteUser() {
   if (!this.selectedUser)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Das Konto wirklich entfernen?`,
        confirmButtonText: $localize`Konto entfernen`,
        value: this.selectedUser?.username
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.users}${this.selectedUser?.id}/`
        ).subscribe(res => {
          const idx = this.users.indexOf(this.selectedUser!);
          if (idx > -1) {
            this.users.splice(idx, 1);
          }
          this.selectedUser = undefined;
        },(error) => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  userAccess(user: User | undefined, infrastructure: Infrastructure): InfrastructureAccess | undefined {
    return user?.access.find(a => a.infrastructure === infrastructure.id);
  }
}
