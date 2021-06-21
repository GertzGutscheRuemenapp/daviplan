import gql from 'graphql-tag'
import { User } from './users';

export const ALL_USERS_QUERY = gql`
    query {
      allUsers{
        id, userName, email, firstName, lastName,
        canEditData, canCreateScenarios, adminAccess
      }
    }
`;

export const CREATE_USER_QUERY = gql`
    mutation createUser($userName: String!, $password: String!){
      createUser(userName: $userName, password: $password){
        user { id, userName }
      }
     }
`;

export const UPDATE_USER_QUERY = gql`
    mutation updateUser($userId: Int!){
      updateUser(id: $userId){
        user{
          id, userName
        }
      }
    }
`;

export type GetUsersQuery = {
  allUsers: User[];
}

