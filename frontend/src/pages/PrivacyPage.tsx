import React from 'react';
import { useTranslation } from 'react-i18next';

const PrivacyPage: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-bg text-text">
      <div className="mx-auto w-full max-w-3xl px-5 py-10">
        <h1 className="mb-6 text-2xl font-bold">{t('privacy.title')}</h1>
        <p className="mb-6 text-sm text-muted">{t('privacy.effective_date')}</p>

        <section className="prose prose-invert max-w-none">
          <h2>{t('privacy.sections.intro_title')}</h2>
          <p>{t('privacy.sections.intro_body')}</p>

          <h2>{t('privacy.sections.collection_title')}</h2>
          <p>{t('privacy.sections.collection_body')}</p>

          <h2>{t('privacy.sections.purpose_title')}</h2>
          <p>{t('privacy.sections.purpose_body')}</p>

          <h2>{t('privacy.sections.retention_title')}</h2>
          <p>{t('privacy.sections.retention_body')}</p>

          <h2>{t('privacy.sections.third_title')}</h2>
          <p>{t('privacy.sections.third_body')}</p>

          <h2>{t('privacy.sections.outsourcing_title')}</h2>
          <p>{t('privacy.sections.outsourcing_body')}</p>

          <h2>{t('privacy.sections.overseas_title')}</h2>
          <p>{t('privacy.sections.overseas_body')}</p>

          <h2>{t('privacy.sections.rights_title')}</h2>
          <p>{t('privacy.sections.rights_body')}</p>

          <h2>{t('privacy.sections.security_title')}</h2>
          <p>{t('privacy.sections.security_body')}</p>

          <h2>{t('privacy.sections.cookie_title')}</h2>
          <p>{t('privacy.sections.cookie_body')}</p>

          <h2>{t('privacy.sections.change_title')}</h2>
          <p>{t('privacy.sections.change_body')}</p>

          <h2>{t('privacy.sections.contact_title')}</h2>
          <p>{t('privacy.sections.contact_body', { email: 'lvlupai.official@gmail.com' })}</p>
        </section>
      </div>
    </div>
  );
};

export default PrivacyPage;


