import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS } from '../../../constants/colors';

const GROUPED_DEPARTMENTS: {
  [letter: string]: { name: string; short: string }[];
} = {
  A: [
    { name: 'Accounting', short: 'ACCT' },
    { name: 'African Cultural Studies', short: 'AFRICAN' },
    { name: 'Anthropology', short: 'ANTHRO' },
  ],
  B: [
    { name: 'Biochemistry', short: 'BIOCHEM' },
    { name: 'Biology', short: 'BIOLOGY' },
  ],
  C: [
    { name: 'Chemistry', short: 'CHEM' },
    { name: 'Computer Sciences', short: 'COMP SCI' },
  ],
  E: [
    { name: 'Economics', short: 'ECON' },
    { name: 'Electrical Engineering', short: 'E C E' },
  ],
  M: [
    { name: 'Mathematics', short: 'MATH' },
    { name: 'Mechanical Engineering', short: 'M E' },
  ],
};

interface CoursesCatalogProps {
  navigation: any;
}

export default function CoursesCatalog({ navigation }: CoursesCatalogProps) {
  const letters = Object.keys(GROUPED_DEPARTMENTS).sort();

  return (
    <View style={styles.container}>
      {letters.map((letter) => (
        <View key={letter} style={styles.subjectCard}>
          <Text style={styles.letterHeading}>{letter}</Text>

          {GROUPED_DEPARTMENTS[letter].map((dept) => (
            <TouchableOpacity
              key={dept.short}
              style={styles.subjectRow}
              onPress={() => {
                // navigation.navigate('DepartmentDetails', { slug: dept.slug })
              }}
              activeOpacity={0.7}
            >
              <View style={styles.dot} />
              <Text style={styles.subjectName}>
                {dept.name} <Text style={styles.shortName}>({dept.short})</Text>
              </Text>
              <Text style={styles.chevron}>›</Text>
            </TouchableOpacity>
          ))}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 24,
  },
  subjectCard: {
    backgroundColor: COLORS.white,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E3E1DB',
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  letterHeading: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.navbarBg,
    marginBottom: 12,
    fontFamily: 'serif',
  },
  subjectRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0EDE8',
    gap: 12,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.navbarBg,
  },
  subjectName: {
    flex: 1,
    fontSize: 15,
    color: '#111',
    fontWeight: '500',
  },
  shortName: {
    color: '#888',
    fontWeight: '400',
    fontSize: 13,
  },
  chevron: {
    fontSize: 18,
    color: '#999',
  },
});