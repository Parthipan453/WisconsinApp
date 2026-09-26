import React from 'react';
import { View, StyleSheet } from 'react-native';
import MainLayout from '../components/MainLayout';
import AcademicHeroSection from './academics/AcademicHeroSection';
import AcademicCardsSection from './academics/AcademicCardsSection';
import LearningSection from './academics/LearningSection';
import StatsSection from './academics/StatsSection';
import SuccessStorySection from './academics/SuccessStorySection';
import ResourcesSection from './academics/ResourcesSection';
import { COLORS } from '../constants/colors';

export default function AcademicsScreen({ navigation }: any) {
  return (
    <MainLayout navigation={navigation} activeScreen="Academics">
      <AcademicHeroSection />
      <AcademicCardsSection navigation={navigation} />
      <LearningSection />
      <StatsSection />
      <SuccessStorySection />
      <ResourcesSection />
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
});