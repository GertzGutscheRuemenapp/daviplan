export type User = {
  id: number;
  userName: string;
  email: string;
  firstName: string;
  lastName: string;
  adminAccess: boolean;
  canCreateScenarios: boolean;
  canEditData: boolean;
  isSuperuser: boolean;
  password: string;
}

export const mockUsers = [
  {
    id: 1,
    userName: 'bla',
    email: 'bla@bla.com',
    firstName: 'Hans',
    lastName: 'Blubb',
    adminAccess: true,
    canCreateScenarios: true,
    canEditData: true,
  },
  {
    id: 2,
    userName: 'bla',
    email: 'bla@bla.com',
    firstName: 'Franz',
    lastName: 'Bumm',
    adminAccess: false,
    canCreateScenarios: true,
    canEditData: true
  },
];
