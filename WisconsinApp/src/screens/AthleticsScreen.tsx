import React from 'react';
import { View, StyleSheet } from 'react-native';
import MainLayout from '../components/MainLayout';
import AthleticsHeaderSection from './athletics/AthleticsHeaderSection';
import FitnessSection from './athletics/FitnessSection';
import { COLORS } from '../constants/colors';

export default function AthleticsScreen({ navigation }: any) {
  return (
    <MainLayout navigation={navigation} activeScreen="Athletics">
      <AthleticsHeaderSection />
      <FitnessSection />
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
});