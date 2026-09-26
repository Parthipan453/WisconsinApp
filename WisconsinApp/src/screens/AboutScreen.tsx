import React from 'react';
import { View, StyleSheet } from 'react-native';
import MainLayout from '../components/MainLayout';
import AboutHeroSection from './about/AboutHeroSection';
import AboutIntroSection from './about/AboutIntroSection';
import RankingSection from './about/RankingSection';
import WisconsinIdeaSection from './about/WisconsinIdeaSection';
import MilestoneSection from './about/MilestoneSection';
import HistorySection from './about/HistorySection';
import StatewideSection from './about/StatewideSection';
import { COLORS } from '../constants/colors';

export default function AboutScreen({ navigation }: any) {
  return (
    <MainLayout navigation={navigation} activeScreen="About">
      <AboutHeroSection />
      <AboutIntroSection />
      <RankingSection />
      <WisconsinIdeaSection />
      <MilestoneSection />
      <HistorySection />
      <StatewideSection />
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
});