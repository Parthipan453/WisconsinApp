import React from 'react';
import { View, StyleSheet } from 'react-native';
import MainLayout from '../components/MainLayout';
import BannerSection from './studentLife/BannerSection';
import FriendsSection from './studentLife/FriendsSection';
import ClubsSection from './studentLife/ClubsSection';
import AthleticsSection from './studentLife/AthleticsSection';
import ArtsSection from './studentLife/ArtsSection';
import TestimonialSection from './studentLife/TestimonialSection';
import CommunitySection from './studentLife/CommunitySection';
import CampusTourSection from './studentLife/CampusTourSection';
import { COLORS } from '../constants/colors';

export default function StudentLifeScreen({ navigation }: any) {
  return (
    <MainLayout navigation={navigation} activeScreen="StudentLife">
      <BannerSection />
      <FriendsSection />
      <ClubsSection />
      <AthleticsSection />
      <ArtsSection />
      <TestimonialSection />
      <CommunitySection />
      <CampusTourSection />
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
});