export type Profile = {
  adminAccess: boolean;
  canCreateScenarios: boolean;
  canEditData: boolean;
}

export type User = {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  isSuperuser: boolean;
  password: string;
  profile: Profile;
}

export const mockUsers = [
  {
    id: 1,
    username: 'bla',
    email: 'bla@bla.com',
    firstName: 'Hans',
    lastName: 'Blubb',
    isSuperuser: false,
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
    profile: {
      adminAccess: false,
      canCreateScenarios: false,
      canEditData: false,
    }
  },
];
