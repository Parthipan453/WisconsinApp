import React from 'react';
import { View, Text, TouchableOpacity, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const STATS = [
  { id: 1, icon: '💰', value: '$1.9B', label: 'Annual research spending (2024)' },
  { id: 2, icon: '💰', value: '2nd', label: 'Most doctorates granted in the nation' },
  { id: 3, icon: '💰', value: '4500+', label: 'Patents granted' },
  { id: 4, icon: '💰', value: '$1.9B', label: 'National research ranking (2024)' },
];

export default function ResearchStatsSection() {
  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.topLine} />
        <Text style={styles.heading}>
          A large research institution with an even larger mission:
          {'\n'}
          to improve lives around the world
        </Text>

        <View style={styles.statsWrapper}>
          {STATS.map((stat) => (
            <View key={stat.id} style={styles.statItem}>
              <View style={styles.statIcon}>
                <Text style={styles.statIconText}>{stat.icon}</Text>
              </View>
              <Text style={styles.statValue}>{stat.value}</Text>
              <Text style={styles.statLabel}>{stat.label}</Text>
            </View>
          ))}
        </View>

        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>
            Discover the impact of UW research
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F3F3F3',
    padding: SIZES.padding,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 10,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 4,
    alignItems: 'center',
  },
  topLine: {
    width: 60,
    height: 5,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 16,
  },
  heading: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  statsWrapper: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: 20,
  },
  statItem: {
    width: '48%',
    alignItems: 'center',
    marginBottom: 20,
  },
  statIcon: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#F6DEDE',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  statIconText: {
    fontSize: 16,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.navbarBg,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#111',
    textAlign: 'center',
    lineHeight: 16,
  },
  button: {
    backgroundColor: COLORS.navbarBg,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 4,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
  },
});