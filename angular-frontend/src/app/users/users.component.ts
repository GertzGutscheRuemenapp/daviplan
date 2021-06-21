import {Component, OnInit} from '@angular/core';
import {Apollo, QueryRef} from 'apollo-angular';
import {User} from './users';
import {ALL_USERS_QUERY, CREATE_USER_QUERY, DELETE_USER_QUERY, GetUsersQuery} from './graphql';

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

  constructor(private apollo: Apollo) {}

  ngOnInit() {
    this.userQuery = this.apollo.watchQuery<GetUsersQuery>({
      query: ALL_USERS_QUERY
    })
    this.userQuery.valueChanges.subscribe((response) =>{
      this.users = response.data.allUsers
    });
  }

  onSelect(user: User): void {
    this.selectedUser = user;
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

  onDeleteUser() {
    if (!this.selectedUser)
      return;
    this.apollo.mutate({
      mutation: DELETE_USER_QUERY,
      variables: {
        id: this.selectedUser.id
      }
    }).subscribe(({ data }) => {
      this.selectedUser = undefined;
      this.userQuery.refetch();
    },(error) => {
      console.log('there was an error sending the query', error);
    });
  }
}
