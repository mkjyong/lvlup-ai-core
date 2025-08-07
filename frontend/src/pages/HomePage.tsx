import React from 'react';
import HeroDuo from '../components/landing/HeroDuo';
import FeaturesSection from '../components/landing/FeaturesSection';
import TestimonialsSection from '../components/landing/TestimonialsSection';
import CTASection from '../components/landing/CTASection';
import Footer from '../components/landing/Footer';
import Header from '../components/landing/Header';
// import HighlightReel from '../components/landing/HighlightReel';

const HomePage: React.FC = () => (
  <>
    <Header />
    <HeroDuo />
    {/* <HighlightReel /> */}
    <FeaturesSection />
    <TestimonialsSection />
    <CTASection />
    <Footer />
  </>
);

export default HomePage; 