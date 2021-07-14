import gql from "graphql-tag";

export const LOGIN_QUERY = gql`
  mutation TokenAuth($username: String!, $password: String!) {
    tokenAuth(username: $username, password: $password) {
      token
      payload
      refreshExpiresIn
    }
}
`;
