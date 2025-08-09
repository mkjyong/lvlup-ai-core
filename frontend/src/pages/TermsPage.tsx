import React from 'react';
import { useTranslation } from 'react-i18next';

const TermsPage: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-bg text-text">
      <div className="mx-auto w-full max-w-3xl px-5 py-10">
        <h1 className="mb-6 text-2xl font-bold">{t('terms.title')}</h1>
        <p className="mb-6 text-sm text-muted">{t('terms.effective_date')}</p>

        <section className="prose prose-invert max-w-none">
          <h2>{t('terms.sections.purpose_title')}</h2>
          <p>{t('terms.sections.purpose_body')}</p>

          <h2>{t('terms.sections.effect_change_title')}</h2>
          <p>{t('terms.sections.effect_change_body')}</p>

          <h2>{t('terms.sections.account_title')}</h2>
          <p>{t('terms.sections.account_body')}</p>

          <h2>{t('terms.sections.billing_title')}</h2>
          <p>{t('terms.sections.billing_body')}</p>

          <h2>{t('terms.sections.use_title')}</h2>
          <p>{t('terms.sections.use_body')}</p>

          <h2>{t('terms.sections.ip_title')}</h2>
          <p>{t('terms.sections.ip_body')}</p>

          <h2>{t('terms.sections.disclaimer_title')}</h2>
          <p>{t('terms.sections.disclaimer_body')}</p>

          <h2>{t('terms.sections.termination_title')}</h2>
          <p>{t('terms.sections.termination_body')}</p>

          <h2>{t('terms.sections.law_title')}</h2>
          <p>{t('terms.sections.law_body')}</p>

          <h2>{t('terms.sections.contact_title')}</h2>
          <p>{t('terms.sections.contact_body', { email: 'lvlupai.official@gmail.com' })}</p>
        </section>
      </div>
    </div>
  );
};

export default TermsPage;


