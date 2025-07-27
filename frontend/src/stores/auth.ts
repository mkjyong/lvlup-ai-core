import { atom } from 'recoil';

export interface User {
  id: string;
  email: string;
}

export const authAtom = atom<{ token: string | null; user: User | null }>({
  key: 'authAtom',
  default: {
    token: localStorage.getItem('token'),
    user: null,
  },
  effects: [
    ({ onSet }) => {
      onSet((newVal) => {
        if (newVal.token) {
          localStorage.setItem('token', newVal.token);
        } else {
          localStorage.removeItem('token');
        }
      });
    },
  ],
}); 