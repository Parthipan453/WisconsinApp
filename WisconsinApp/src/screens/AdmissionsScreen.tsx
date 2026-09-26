import React from 'react';
import { View, StyleSheet } from 'react-native';
import MainLayout from '../components/MainLayout';
import AdmissionBannerSection from './admissions/AdmissionBannerSection';
import AdmissionOptionsSection from './admissions/AdmissionOptionsSection';
import TuitionSection from './admissions/TuitionSection';
import PromiseSection from './admissions/PromiseSection';
import ProSchoolsSection from './admissions/ProSchoolsSection';
import MadisonSection from './admissions/MadisonSection';
import UWReportSection from './admissions/UWReportSection';
import { COLORS } from '../constants/colors';

export default function AdmissionsScreen({ navigation }: any) {
  return (
    <MainLayout navigation={navigation} activeScreen="Admissions">
      <AdmissionBannerSection />
      <AdmissionOptionsSection />
      <TuitionSection />
      <PromiseSection />
      <ProSchoolsSection />
      <MadisonSection />
      <UWReportSection />
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
});