import React from 'react';
import { View, StyleSheet } from 'react-native';
import MainLayout from '../components/MainLayout';
import ResearchHeroSection from './research/ResearchHeroSection';
import ResearchIntroSection from './research/ResearchIntroSection';
import DiscoverySection from './research/DiscoverySection';
import ResearchStorySection from './research/ResearchStorySection';
import ResearchImpactSection from './research/ResearchImpactSection';
import ResearchStatsSection from './research/ResearchStatsSection';
import LatestNewsSection from './research/LatestNewsSection';
import InnovationSection from './research/InnovationSection';
import { COLORS } from '../constants/colors';

export default function ResearchScreen({ navigation }: any) {
  return (
    <MainLayout navigation={navigation} activeScreen="Research">
      <ResearchHeroSection />
      <ResearchIntroSection />
      <DiscoverySection />
      <ResearchStorySection />
      <ResearchImpactSection />
      <ResearchStatsSection />
      <LatestNewsSection />
      <InnovationSection />
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
});