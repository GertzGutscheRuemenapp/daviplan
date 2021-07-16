import { AfterViewInit, Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BreakpointObserver, Breakpoints } from "@angular/cdk/layout";
import { map } from "rxjs/operators";
import { MatDialog } from '@angular/material/dialog';
import { User } from '../../login/users';
import { ConfirmDialogComponent } from '../../dialogs/confirm-dialog.component';
import { DataCardComponent } from '../../dash/data-card.component'
import { FormBuilder, FormControl, FormGroup, Validators } from "@angular/forms";
import { RestAPI } from "../../rest-api";
import { Observable } from "rxjs";

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})

export class UsersComponent implements AfterViewInit  {

  @ViewChild('accountCard') accountCard?: DataCardComponent;
  @ViewChild('permissionCard') permissionCard?: DataCardComponent;
  @ViewChild('createUser') createUserTemplate?: TemplateRef<any>;
  accountForm!: FormGroup;
  permissionForm!: FormGroup;
  createUserForm: FormGroup;
  users: User[] = [];
  selectedUser?: User;
  changePassword: boolean = false;

  layout = this.breakpointObserver.observe(Breakpoints.Handset).pipe(
    map(({ matches }) => {
      if (matches) {
        return {
          columns: 1,
          userList: { cols: 1, rows: 1 },
          account: { cols: 1, rows: 2 },
          permissions: { cols: 1, rows: 2 },
          dataAccess: { cols: 1, rows: 2 },
        };
      }

      return {
        columns: 3,
        userList: { cols: 1, rows: 2 },
        account: { cols: 1, rows: 1 },
        permissions: { cols: 1, rows: 1 },
        dataAccess: { cols: 1, rows: 1 },
      };
    })
  );
  Object = Object;

  constructor(private http: HttpClient, private breakpointObserver: BreakpointObserver,
              private dialog: MatDialog, private formBuilder: FormBuilder, private rest: RestAPI) {
    this.createUserForm = this.formBuilder.group({
      username: new FormControl('', Validators.required),
      password: new FormControl('', Validators.required),
      confirmPass: new FormControl('', Validators.required)
    });
  }

  ngAfterViewInit() {
    this.getUsers();
    this.setupAccountCard();
    this.setupPermissionCard();
  }

  getUsers(): Observable<User[]> {
    let query = this.http.get<User[]>(this.rest.URLS.users);
    query.subscribe((users)=>{
      this.users = users.slice().sort((a,b) =>
        (!a.isSuperuser && b.isSuperuser)? 1 : (a.isSuperuser && !b.isSuperuser)? -1 :
          (a.username > b.username)? 1 : (a.username < b.username)? -1 : 0)
    })
    return query;
  }

  setupAccountCard(){
    if (!this.accountCard) return;
    this.accountCard.dialogConfirmed.subscribe((ok)=>{
      this.accountForm.setErrors(null);
      // display errors for all fields even if not touched
      this.accountForm.markAllAsTouched();
      if (this.accountForm.invalid) return;
      let user = this.accountForm.value.user;
      let attributes: any = {
          id: this.selectedUser?.id,
          username: user.username,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          password: null
      }
      if (this.accountForm.value.changePass){
        let pass = this.accountForm.value.password
        if (pass != this.accountForm.value.confirmPass){
          this.accountForm.controls['confirmPass'].setErrors({'notMatching': true});
          return;
        }
        attributes.password = pass;
      }
      this.accountCard?.setLoading(true);
      this.http.patch<User>(`${this.rest.URLS.users}${this.selectedUser?.id}/`, attributes
      ).subscribe(data => {
        this.accountCard?.closeDialog();
        this.refresh(data.id);
      },(error) => {
        // ToDo: set specific errors to fields
        this.accountForm.setErrors(error.error);
        this.accountCard?.setLoading(false);
      });
    })
    this.accountCard.dialogClosed.subscribe((ok)=>{
      // reset form on cancel
      if (!ok){
        this.changePassword = false;
        this.accountForm.controls['password'].disable();
        this.accountForm.controls['confirmPass'].disable();
        this.accountForm.reset({
          user: this.selectedUser,
          changePass: this.changePassword,
          password: '',
          confirmPass: ''
        });
      }
    })
  }

  setupPermissionCard() {
    if (!this.permissionCard) return;
    this.permissionCard.dialogConfirmed.subscribe((ok)=>{
      this.permissionForm.setErrors(null);
      let profile = this.permissionForm.value.profile;
      let attributes = {
        profile: {
          adminAccess: profile.adminAccess,
          canCreateScenarios: profile.canCreateScenarios,
          canEditData: profile.canEditData
        }
      }
      this.permissionCard?.setLoading(true);
      this.http.patch<User>(`${this.rest.URLS.users}${this.selectedUser?.id}/`, attributes
      ).subscribe(user => {
        this.permissionCard?.closeDialog();
        this.refresh(user.id);
      },(error) => {
        this.permissionForm.setErrors(error.error);
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

  refresh(userId?: number): void {
    this.getUsers().subscribe( data => {
      if (userId != undefined){
        let user = this.users.find(user => user.id === userId);
        this.onSelect(user as User);
      }
      else
        this.selectedUser = undefined;
    });
  }

  onSelect(user: User) {
    this.selectedUser = user;
    this.accountForm = this.formBuilder.group({
      user: this.formBuilder.group(this.selectedUser),
      changePass: this.changePassword,
      password: new FormControl({value: '', disabled: !this.changePassword}),
      confirmPass: new FormControl({value: '', disabled: !this.changePassword})
    });
    let userControl: any = this.accountForm.get('user');
    userControl.get('email').setValidators([Validators.email])
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
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.createUserForm.setErrors(null);
      // display errors for all fields even if not touched
      this.createUserForm.markAllAsTouched();
      if (this.createUserForm.invalid) return;
      let username = this.createUserForm.value.username;
      let password = this.createUserForm.value.password;
      if (password != this.createUserForm.value.confirmPass){
        this.createUserForm.controls['confirmPass'].setErrors({'notMatching': true});
        return;
      }
      dialogRef.componentInstance.isLoading = true;
      let attributes = {
        username: username,
        password: password
      };
      this.http.post<User>(this.rest.URLS.users, attributes
      ).subscribe(user => {
        this.refresh(user.id);
        dialogRef.close();
      },(error) => {
        this.createUserForm.setErrors(error.error);
        dialogRef.componentInstance.isLoading = false;
      });
    });
  }

  onDeleteUser() {
   if (!this.selectedUser)
      return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '300px',
      data: {
        title: 'Nutzer löschen',
        message: `Möchten sie den Nutzer "${this.selectedUser.username}" wirklich löschen?`,
        closeOnConfirm: true
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed === true) {
        this.http.delete(`${this.rest.URLS.users}${this.selectedUser?.id}/`
        ).subscribe(res => {
          this.refresh();
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }
}
