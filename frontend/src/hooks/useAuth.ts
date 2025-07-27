import { useRecoilState } from 'recoil';
import { authAtom } from '../stores/auth';

export const useAuth = () => {
  const [auth, setAuth] = useRecoilState(authAtom);

  const login = (token: string) => {
    setAuth({ ...auth, token });
  };

  const logout = () => {
    setAuth({ token: null, user: null });
  };

  return {
    ...auth,
    login,
    logout,
    isAuthenticated: Boolean(auth.token),
  };
}; 