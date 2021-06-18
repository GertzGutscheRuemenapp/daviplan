export interface Users {
  id: number;
  user_name: string;
  email: string;
  first_name: string;
  last_name: string;
  admin_access: boolean;
  can_create_scenarios: boolean;
  can_edit_data: boolean;
}

export const users = [
  {
    id: 1,
    user_name: 'bla';
    email: 'bla@bla.com';
    first_name: 'Hans';
    last_name: 'Blubb';
    admin_access: true;
    can_create_scenarios: true;
    can_edit_data: true;
  },
  {
    id: 2,
    user_name: 'bla';
    email: 'bla@bla.com';
    first_name: 'Franz';
    last_name: 'Bumm';
    admin_access: false;
    can_create_scenarios: true;
    can_edit_data: true;
  },
];
