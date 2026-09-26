import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

import HomeScreen from '../screens/HomeScreen';
import AcademicsScreen from '../screens/AcademicsScreen';
import AdmissionsScreen from '../screens/AdmissionsScreen';
import StudentLifeScreen from '../screens/StudentLifeScreen';
import ResearchScreen from '../screens/ResearchScreen';
import AthleticsScreen from '../screens/AthleticsScreen';
import AboutScreen from '../screens/AboutScreen';
import MajorsScreen from '../screens/academics/majors/MajorsScreen';

import CoursesScreen from '../screens/academics/courses/CoursesScreen';

const Stack = createStackNavigator();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Academics" component={AcademicsScreen} />
        <Stack.Screen name="Admissions" component={AdmissionsScreen} />
        <Stack.Screen name="StudentLife" component={StudentLifeScreen} />
        <Stack.Screen name="Research" component={ResearchScreen} />
        <Stack.Screen name="Athletics" component={AthleticsScreen} />
        <Stack.Screen name="About" component={AboutScreen} />
        <Stack.Screen name="Majors" component={MajorsScreen} />
        <Stack.Screen name="Courses" component={CoursesScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}