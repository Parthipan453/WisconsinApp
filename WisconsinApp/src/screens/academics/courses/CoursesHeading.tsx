import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS } from '../../../constants/colors';

export default function CoursesHeading() {
  return (
    <View style={styles.container}>
      <View style={styles.headingRow}>
        <View style={styles.pageIcon}>
          <Text style={styles.iconText}>📖</Text>
        </View>
        <View style={styles.headingText}>
          <Text style={styles.title}>Courses</Text>
          <View style={styles.redLine} />
        </View>
      </View>

      <Text style={styles.description}>
        Courses listed below, separated by subject, are active as of the
        fall 2026 term. Courses can be updated three times per year,
        to coincide with the priority enrollment time period for
        upcoming terms.
      </Text>

      <TouchableOpacity style={styles.printOptions}>
        <View style={styles.printLeft}>
          <View style={styles.printIconCircle}>
            <Text style={styles.printIcon}>🖨️</Text>
          </View>
          <Text style={styles.printText}>Print Options</Text>
        </View>
        <Text style={styles.chevron}>▼</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  headingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  pageIcon: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 28,
  },
  headingText: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111',
    marginBottom: 6,
    fontFamily: 'serif',
  },
  redLine: {
    width: 40,
    height: 3,
    backgroundColor: COLORS.navbarBg,
  },
  description: {
    fontSize: 14,
    lineHeight: 22,
    color: '#555',
    marginBottom: 20,
  },
  printOptions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E3E1DB',
    paddingVertical: 12,
    paddingHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  printLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  printIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#f6e2e3',
    justifyContent: 'center',
    alignItems: 'center',
  },
  printIcon: {
    fontSize: 16,
  },
  printText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111',
  },
  chevron: {
    fontSize: 12,
    color: '#999',
  },
});