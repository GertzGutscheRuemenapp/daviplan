import { Component, OnInit } from '@angular/core';
import { Apollo, gql } from 'apollo-angular';
import { map } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { mockUsers, User, UserQuery } from './users';

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})
export class UsersComponent implements OnInit {

  users!: Observable<User[]>;
  selectedUser?: User;

  constructor(private apollo: Apollo) {}

  ngOnInit() {
    this.users = this.apollo.watchQuery<UserQuery>({
      query: gql`
        query {
          allUsers{
            id, userName, canEditData, canCreateScenarios, adminAccess
          }
        }
      `
    }).valueChanges.pipe(map(result => result.data.allUsers));
  }

  onSelect(user: User): void {
    this.selectedUser = user;
  }

}
