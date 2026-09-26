import React from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import MainLayout from '../../../components/course/CourseLayout';
import CoursesBreadcrumb from './CoursesBreadcrumb';
import CoursesHeading from './CoursesHeading';
import CoursesSkipLetters from './CoursesSkipLetters';
import CoursesRightSidebar from './CoursesRightSidebar';
import CoursesCatalog from './CoursesCatalog';
import { COLORS } from '../../../constants/colors';

export default function CoursesScreen({ navigation }: any) {
  return (
    <MainLayout navigation={navigation} activeScreen="Courses">
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
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
      </ScrollView>
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
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