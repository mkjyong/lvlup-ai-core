import { atom } from 'recoil';
import { jwtDecode as jwt_decode } from 'jwt-decode';

export interface User {
  id: string;
  email: string;
}

export const authAtom = atom<{ token: string | null; user: User | null }>({
  key: 'authAtom',
  default: (() => {
    const rawToken = localStorage.getItem('token');
    let validToken: string | null = null;
    if (rawToken) {
      try {
                const { exp } = jwt_decode<{ exp?: number }>(rawToken);
        if (exp && exp * 1000 > Date.now()) {
          validToken = rawToken;
        } else {
          localStorage.removeItem('token');
        }
      } catch {
        // decode 실패 시 토큰 제거
        localStorage.removeItem('token');
      }
    }
    return {
      token: validToken,
      user: null,
    };
  })(),
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