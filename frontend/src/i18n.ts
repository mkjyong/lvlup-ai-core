import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enTranslation from './locales/en/translation.json';
import koTranslation from './locales/ko/translation.json';

export const defaultNS = 'translation';

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslation },
      ko: { translation: koTranslation },
    },
    fallbackLng: 'ko',
    supportedLngs: ['en', 'ko'],
    interpolation: {
      escapeValue: false, // React already escapes
    },
    detection: {
      order: ['navigator', 'htmlTag', 'localStorage', 'cookie', 'path', 'subdomain'],
      caches: ['localStorage', 'cookie'],
    },
  });

export default i18n;
