import React from 'react';
import { View, StyleSheet } from 'react-native';
import MainLayout from '../components/MainLayout';
import HeroSection from './home/HeroSection';
import TrendingSection from './home/TrendingSection';
import ResearchSection from './home/ResearchSection';
import DiscoveriesSection from './home/DiscoveriesSection';
import PurposeSection from './home/PurposeSection';
import { COLORS } from '../constants/colors';

export default function HomeScreen({ navigation }: any) {
  return (
    <MainLayout navigation={navigation} activeScreen="Home">
      <HeroSection navigation={navigation} />
      <TrendingSection />
      <ResearchSection />
      <DiscoveriesSection />
      <PurposeSection />
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
});