import { useRecoilState } from 'recoil';
import { uiAtom } from '../stores/ui';

export const useTheme = () => {
  const [ui, setUi] = useRecoilState(uiAtom);

  const toggleTheme = () => {
    setUi({ theme: ui.theme === 'dark' ? 'light' : 'dark' });
  };

  return { ...ui, toggleTheme };
}; 