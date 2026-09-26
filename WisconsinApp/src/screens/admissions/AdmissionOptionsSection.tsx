import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const OPTIONS = [
  {
    id: 1,
    icon: '🏛️',
    title: 'Undergraduate Admissions',
    description: 'Start your journey as a future Badger.',
  },
  {
    id: 2,
    icon: '🏛️',
    title: 'Graduate Admissions',
    description: 'Continue your academic excellence.',
  },
];

export default function AdmissionOptionsSection() {
  return (
    <View style={styles.container}>
      <Text style={styles.heading}>
        <Text style={styles.bold}>UW-Madison</Text> is a world-renowned academic
        institution, dedicated to making the college experience attainable and
        affordable for every talented scholar.
      </Text>

      <Text style={styles.subtext}>
        Being a Badger means{' '}
        <Text style={styles.highlight}>
          dreaming big and then doing something bigger.
        </Text>
      </Text>

      {OPTIONS.map((option) => (
        <TouchableOpacity key={option.id} style={styles.card}>
          <View style={styles.iconCircle}>
            <Text style={styles.iconText}>{option.icon}</Text>
          </View>
          <View style={styles.cardContent}>
            <Text style={styles.cardTitle}>{option.title}</Text>
            <Text style={styles.cardDescription}>{option.description}</Text>
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    padding: SIZES.padding * 1.5,
  },
  heading: {
    fontSize: 18,
    lineHeight: 26,
    color: '#1A1A1A',
    textAlign: 'center',
    fontWeight: '500',
    marginBottom: 12,
  },
  bold: {
    fontWeight: '700',
    fontSize: 20,
  },
  subtext: {
    fontSize: 16,
    color: '#333',
    textAlign: 'center',
    marginBottom: 24,
  },
  highlight: {
    color: COLORS.navbarBg,
    fontWeight: '600',
  },
  card: {
    backgroundColor: '#F1D1D1',
    borderRadius: 8,
    padding: 20,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 5,
    borderBottomColor: COLORS.navbarBg,
  },
  iconCircle: {
    width: 55,
    height: 55,
    borderRadius: 28,
    backgroundColor: '#F7E3E3',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  iconText: {
    fontSize: 26,
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  cardDescription: {
    fontSize: 14,
    color: '#555',
  },
});