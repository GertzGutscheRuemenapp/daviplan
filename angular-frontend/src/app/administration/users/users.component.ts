import {AfterViewInit, Component, OnInit, ViewChild} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import { BreakpointObserver, Breakpoints } from "@angular/cdk/layout";
import { map } from "rxjs/operators";
import { MAT_DIALOG_DATA, MatDialogRef, MatDialog } from '@angular/material/dialog';
import { User } from './users';
import { ALL_USERS_QUERY, CREATE_USER_QUERY, DELETE_USER_QUERY, GetUsersQuery,
         UPDATE_USER_QUERY, UPDATE_ACCOUNT_QUERY, UPDATE_ACCOUNT_QUERY_WO_PASS,
         UPDATE_PERMISSIONS_QUERY } from './graphql';
import { ConfirmDialogComponent } from '../../dialogs/confirm-dialog.component';
import { DataCardComponent } from '../../dash/data-card.component'
import {Observable} from "rxjs";
import {FormBuilder, FormControl, FormGroup, Validators} from "@angular/forms";

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})

export class UsersComponent implements AfterViewInit  {

  @ViewChild('accountCard') accountCard?: DataCardComponent;
  @ViewChild('permissionCard') permissionCard?: DataCardComponent;
  accountForm!: FormGroup;
  permissionForm!: FormGroup;
  userQuery!: QueryRef<GetUsersQuery>;
  users: User[] = [];
  selectedUser?: User;
  newUserName: String = '';
  newUserPassword: String = '';
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

  constructor(private apollo: Apollo, private breakpointObserver: BreakpointObserver,
              public dialog: MatDialog, private formBuilder: FormBuilder) {
  }

  ngAfterViewInit() {
    this.userQuery = this.apollo.watchQuery<GetUsersQuery>({
      query: ALL_USERS_QUERY
    })
    this.userQuery.valueChanges.subscribe((response) =>{
      this.users = response.data.allUsers;
      this.users = this.users.slice().sort((a,b) => (a.userName > b.userName)? 1 : (a.userName < b.userName)? -1 : 0)
    });
    this.setupAccountCard();
    this.setupPermissionCard();
  }

  setupAccountCard(){
    if (!this.accountCard) return;
    this.accountCard.dialogConfirmed.subscribe((ok)=>{
      this.accountForm.setErrors(null);
      // display errors for all fields even if not touched
      this.accountForm.markAllAsTouched();
      if (this.accountForm.invalid) return;
      let user = this.accountForm.value.user;
      let variables: any = {
          id: this.selectedUser?.id,
          userName: user.userName,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName
      }
      let mutation = UPDATE_ACCOUNT_QUERY_WO_PASS;
      if (this.accountForm.value.changePass){
        let pass = this.accountForm.value.password
        if (pass != this.accountForm.value.confirmPass){
          this.accountForm.controls['confirmPass'].setErrors({'notMatching': true});
          return;
        }
        variables.password = pass;
        mutation = UPDATE_ACCOUNT_QUERY;
      }
      this.accountCard?.setLoading(true);
      this.apollo.mutate({
        mutation: mutation,
        variables: variables
      }).subscribe(({ data }) => {
        this.accountCard?.closeDialog();
        this.refresh((data as any).updateUser.user.id);
      },(error) => {
        this.accountForm.setErrors({ 'error': error })
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
      let user = this.permissionForm.value.user;
      let variables: any = {
        id: this.selectedUser?.id,
        adminAccess: user.adminAccess,
        canCreateScenarios: user.canCreateScenarios,
        canEditData: user.canEditData
      }
      this.permissionCard?.setLoading(true);
      this.apollo.mutate({
        mutation: UPDATE_PERMISSIONS_QUERY,
        variables: variables
      }).subscribe(({ data }) => {
        this.permissionCard?.closeDialog();
        this.refresh((data as any).updateUser.user.id);
      },(error) => {
        this.permissionForm.setErrors({ 'error': error })
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
    this.userQuery.refetch().then( res => {
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
      user: this.formBuilder.group(this.selectedUser)
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
    this.apollo.mutate({
      mutation: CREATE_USER_QUERY,
      variables: {
        userName: this.newUserName,
        password: this.newUserPassword
      }
    }).subscribe(({ data }) => {
      this.refresh((data as any).createUser.user.id);
    },(error) => {
    });
  }

  onUpdateUser() {
    if (!this.selectedUser)
      return;
    this.apollo.mutate({
      mutation: UPDATE_USER_QUERY,
      variables: {
        id: this.selectedUser.id,
        userName: this.selectedUser.userName,
        email: this.selectedUser.email,
        firstName: this.selectedUser.firstName,
        lastName: this.selectedUser.lastName,
        canEditData: this.selectedUser.canEditData,
        canCreateScenarios: this.selectedUser.canCreateScenarios,
        adminAccess: this.selectedUser.adminAccess
      }
    }).subscribe(({ data }) => {
      let userId = (data as any).updateUser.user.id;
      this.userQuery.refetch().then( res => {
        let user = this.users.find(user => user.id === userId);
        this.selectedUser = Object.assign({}, user);
      });
    },(error) => {
      console.log('there was an error sending the query', error);
    });

  }

  onDeleteUser() {
   if (!this.selectedUser)
      return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '300px',
      data: {
        title: 'Nutzer löschen',
        message: `Möchten sie den Nutzer "${this.selectedUser.userName}" wirklich löschen?`
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed === true) {
        this.apollo.mutate({
          mutation: DELETE_USER_QUERY,
          variables: {
            id: this.selectedUser!.id
          }
        }).subscribe(({ data }) => {
          this.refresh();
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }
}
