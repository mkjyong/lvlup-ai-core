import { atom } from 'recoil';

export const uiAtom = atom<{ theme: 'light' | 'dark' }>({
  key: 'uiAtom',
  default: {
    theme: (document.documentElement.classList.contains('dark') ? 'dark' : 'light') as
      | 'light'
      | 'dark',
  },
  effects: [
    ({ onSet }) => {
      onSet((val) => {
        if (val.theme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
        localStorage.setItem('theme', val.theme);
      });
    },
  ],
}); 