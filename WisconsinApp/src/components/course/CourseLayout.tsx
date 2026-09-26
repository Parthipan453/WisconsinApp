import React from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import CourseTopBar from './CourseTopBar';
import CourseHeader from './CourseHeader';
import CourseNav from './CourseNav';
import CourseFooter from './CourseFooter';
import { COLORS } from '../../constants/colors';

interface CourseLayoutProps {
  children: React.ReactNode;
  navigation: any;
  activeTab?: string;
}

export default function CourseLayout({
  children,
  navigation,
  activeTab = 'courses',
}: CourseLayoutProps) {
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <CourseTopBar />
        <CourseHeader />
        <CourseNav navigation={navigation} activeTab={activeTab} />

        {children}

        <CourseFooter />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: 40,
  },
});