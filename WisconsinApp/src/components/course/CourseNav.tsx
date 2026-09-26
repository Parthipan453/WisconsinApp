import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { COLORS } from '../../constants/colors';

interface CourseNavProps {
  navigation: any;
  activeTab?: string;
}

const NAV_ITEMS = [
  { id: 'undergraduate', label: 'Undergraduate', icon: '📖', screen: 'Home' },
  { id: 'graduate', label: 'Graduate/Professional', icon: '🎓', screen: 'Home' },
  { id: 'nondegree', label: 'Nondegree', icon: '👥', screen: 'Home' },
  { id: 'courses', label: 'Courses', icon: '📋', screen: 'Courses' },
];

export default function CourseNav({
  navigation,
  activeTab = 'courses',
}: CourseNavProps) {
  return (
    <View style={styles.container}>
      <View style={styles.navGrid}>
        {NAV_ITEMS.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={[
              styles.navItem,
              activeTab === item.id && styles.navItemActive,
            ]}
            onPress={() => {
              if (item.screen) {
                navigation.navigate(item.screen);
              }
            }}
            activeOpacity={0.7}
          >
            <Text style={styles.navIcon}>{item.icon}</Text>
            <Text
              style={[
                styles.navText,
                activeTab === item.id && styles.navTextActive,
              ]}
              numberOfLines={1}
            >
              {item.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.navbarBg,
  },
  navGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 4,
    paddingVertical: 4,
  },
  navItem: {
    width: '50%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    gap: 6,
    borderBottomWidth: 3,
    borderBottomColor: 'transparent',
  },
  navItemActive: {
    borderBottomColor: COLORS.white,
  },
  navIcon: {
    fontSize: 14,
  },
  navText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '500',
    flexShrink: 1,
  },
  navTextActive: {
    fontWeight: '700',
  },
});