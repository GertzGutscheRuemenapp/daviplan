export type Profile = {
  adminAccess: boolean;
  canCreateScenarios: boolean;
  canEditData: boolean;
}

export interface User {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  isSuperuser: boolean;
  password: string;
  profile: Profile;
}

export const mockUsers: User[] = [
  {
    id: 1,
    username: 'bla',
    email: 'bla@bla.com',
    firstName: 'Hans',
    lastName: 'Blubb',
    isSuperuser: false,
    password: '',
    profile: {
      adminAccess: true,
      canCreateScenarios: true,
      canEditData: true,
    }
  },
  {
    id: 2,
    username: 'admin',
    email: 'bla2@bla.com',
    firstName: 'Franz',
    lastName: 'Bumm',
    isSuperuser: true,
    password: '',
    profile: {
      adminAccess: false,
      canCreateScenarios: false,
      canEditData: false,
    }
  },
];
