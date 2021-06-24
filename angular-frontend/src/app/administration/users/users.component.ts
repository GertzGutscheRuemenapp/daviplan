import { Component, OnInit } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import { BreakpointObserver, Breakpoints } from "@angular/cdk/layout";
import { map } from "rxjs/operators";
import { MatDialog } from '@angular/material/dialog';
import { User } from './users';
import { ALL_USERS_QUERY, CREATE_USER_QUERY, DELETE_USER_QUERY, GetUsersQuery, UPDATE_USER_QUERY } from './graphql';
import { ConfirmDialogComponent } from '../../dialogs/confirm-dialog.component';

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})

export class UsersComponent implements OnInit {

  userQuery!: QueryRef<GetUsersQuery>;
  users: User[] = [];
  selectedUser?: User;
  newUserName: String = '';
  newUserPassword: String = '';

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

  constructor(private apollo: Apollo, private breakpointObserver: BreakpointObserver, public dialog: MatDialog) {}

  ngOnInit() {
    this.userQuery = this.apollo.watchQuery<GetUsersQuery>({
      query: ALL_USERS_QUERY
    })
    this.userQuery.valueChanges.subscribe((response) =>{
      this.users = response.data.allUsers
    });
  }

  onSelect(user: User): void {
    this.selectedUser = Object.assign({}, user);
  }

  onCreateUser() {
    this.apollo.mutate({
      mutation: CREATE_USER_QUERY,
      variables: {
        userName: this.newUserName,
        password: this.newUserPassword
      }
    }).subscribe(({ data }) => {
      let userId = (data as any).createUser.user.id;
      this.userQuery.refetch().then( res => {
        this.selectedUser = this.users.find(user => user.id === userId);
      });
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
          this.selectedUser = undefined;
          this.userQuery.refetch();
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }
}
