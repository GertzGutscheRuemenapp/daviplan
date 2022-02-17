export type Profile = {
  adminAccess: boolean;
  canCreateProcess: boolean;
  canEditBasedata: boolean;
}

export type InfrastructureAccess = {
  infrastructure: number,
  allowSensitiveData: boolean
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
  access: InfrastructureAccess[];
}

export const mockUsers: User[] = [
  {
    id: 1,
    username: 'bla',
    email: 'bla@bla.com',
    firstName: 'Sascha',
    lastName: 'Schmidt',
    isSuperuser: false,
    password: '',
    profile: {
      adminAccess: true,
      canCreateProcess: true,
      canEditBasedata: true,
    },
    access: []
  },
  {
    id: 2,
    username: 'admin',
    email: 'bla2@bla.com',
    firstName: 'Hannah',
    lastName: 'Hansen',
    isSuperuser: true,
    password: '',
    profile: {
      adminAccess: false,
      canCreateProcess: false,
      canEditBasedata: false,
    },
    access: []
  },
];
