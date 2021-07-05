import {AfterViewInit, Component, OnInit, ViewChild} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import { BreakpointObserver, Breakpoints } from "@angular/cdk/layout";
import { map } from "rxjs/operators";
import { MAT_DIALOG_DATA, MatDialogRef, MatDialog } from '@angular/material/dialog';
import { User } from './users';
import { ALL_USERS_QUERY, CREATE_USER_QUERY, DELETE_USER_QUERY, GetUsersQuery, UPDATE_USER_QUERY, UPDATE_ACCOUNT_QUERY, UPDATE_ACCOUNT_QUERY_WO_PASS } from './graphql';
import { ConfirmDialogComponent } from '../../dialogs/confirm-dialog.component';
import { DataCardComponent } from '../../dash/data-card.component'
import {Observable} from "rxjs";
import {FormBuilder, FormControl, FormGroup} from "@angular/forms";

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})

export class UsersComponent implements OnInit  {

  @ViewChild('accountCard') accountCard?: DataCardComponent;
  userQuery!: QueryRef<GetUsersQuery>;
  users: User[] = [];
  selectedUser?: User;
  newUserName: String = '';
  newUserPassword: String = '';
  accountForm!: FormGroup;
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

  ngOnInit() {
    this.userQuery = this.apollo.watchQuery<GetUsersQuery>({
      query: ALL_USERS_QUERY
    })
    this.userQuery.valueChanges.subscribe((response) =>{
      this.users = response.data.allUsers
    });
  }

  @ViewChild('accountCard') set content(content: DataCardComponent) {
    if(content) {
      this.accountCard = content;
      this.accountCard.dialogConfirmed.subscribe((ok)=>{
        if (this.accountForm.value.changePass){
          if (!this.accountForm.value.password){
            return;
          }
          else if (this.accountForm.value.password != this.accountForm.value.passConfirm){
            this.accountForm.controls['password'].setErrors({'notMatching': true});
            return;
          }
        }
        this.accountCard?.setLoading(true);
        let user = this.accountForm.value.user;
        if (!user.userName) return;
        this.apollo.mutate({
          mutation: UPDATE_ACCOUNT_QUERY_WO_PASS,
          variables: {
            id: this.selectedUser?.id,
            userName: user.userName,
            email: user.email,
            firstName: user.firstName,
            lastName: user.lastName
          }
        }).subscribe(({ data }) => {
          this.accountCard?.setLoading(false);
          this.accountCard?.closeDialog();
          this.refresh((data as any).updateUser.user.id);
        },(error) => {
          console.log('there was an error sending the query', error);
          this.accountForm.setErrors({ 'error': error })
          this.accountCard?.setLoading(false);
        });
      })
      this.accountCard.dialogClosed.subscribe(()=>{
        this.changePassword = false;
        this.accountForm.controls['password'].disable();
        this.accountForm.controls['passConfirm'].disable();
        this.accountForm.reset({
          user: this.selectedUser,
          changePass: this.changePassword,
          password: '',
          passConfirm: ''
        });
      })
    }
  }

  refresh(userId?: number): void {
    this.userQuery.refetch().then( res => {
      if (userId != undefined){
        let user = this.users.find(user => user.id === userId);
        this.selectedUser = user;
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
      passConfirm: new FormControl({value: '', disabled: !this.changePassword})
    });
  }

  onTogglePassChange(checked: boolean) {
    this.changePassword = checked;
    if (checked){
      this.accountForm.controls['password'].enable();
      this.accountForm.controls['passConfirm'].enable();
    }
    else {
      this.accountForm.controls['password'].disable();
      this.accountForm.controls['passConfirm'].disable();
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
      console.log('there was an error sending the query', error);
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
