import React from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import CourseLayout from '../../../components/course/CourseLayout';
import CoursesBreadcrumb from './CoursesBreadcrumb';
import CoursesHeading from './CoursesHeading';
import CoursesSkipLetters from './CoursesSkipLetters';
import CoursesRightSidebar from './CoursesRightSidebar';
import CoursesCatalog from './CoursesCatalog';
import { COLORS } from '../../../constants/colors';

export default function CoursesScreen({ navigation }: any) {
  return (
    <CourseLayout navigation={navigation} activeTab="courses">
      <View style={styles.content}>
        <CoursesBreadcrumb />
        <CoursesHeading />

        <View style={styles.topSection}>
          <View style={styles.leftColumn}>
            <CoursesSkipLetters />
          </View>
          <View style={styles.rightColumn}>
            <CoursesRightSidebar />
          </View>
        </View>

        <CoursesCatalog navigation={navigation} />
      </View>
    </CourseLayout>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: 16,
    paddingBottom: 40,
    backgroundColor: COLORS.white,
  },
  topSection: {
    flexDirection: 'column',
    gap: 20,
    marginBottom: 30,
  },
  leftColumn: {
    width: '100%',
  },
  rightColumn: {
    width: '100%',
  },
});