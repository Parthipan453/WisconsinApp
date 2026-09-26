import React from 'react';
import { View, StyleSheet } from 'react-native';
import MainLayout from '../../../components/MainLayout';
import MajorsBannerSection from './MajorsBannerSection';
import MajorsIntroSection from './MajorsIntroSection';
import { COLORS } from '../../../constants/colors';

export default function MajorsScreen({ navigation }: any) {
  return (
    <MainLayout navigation={navigation} activeScreen="Majors">
      <MajorsBannerSection />
      <MajorsIntroSection navigation={navigation} />
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
});