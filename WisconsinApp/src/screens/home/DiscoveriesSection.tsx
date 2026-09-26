import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const DISCOVERIES = [
  { id: 1, image: require('../../assets/images/d1.jpg'), title: 'Discovering stem cells' },
  { id: 2, image: require('../../assets/images/d2.jpg'), title: 'Discovering stem cells' },
  { id: 3, image: require('../../assets/images/d3.jpg'), title: 'Discovering stem cells' },
  { id: 4, image: require('../../assets/images/d4.jpg'), title: 'Discovering stem cells' },
];

export default function DiscoveriesSection() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>More UW–Madison discoveries</Text>
      <Text style={styles.subtitle}>
        Explore the latest breakthroughs and stories from our researchers.
      </Text>

      <View style={styles.grid}>
        {DISCOVERIES.map((item) => (
          <View key={item.id} style={styles.card}>
            <Image source={item.image} style={styles.cardImg} />
            <Text style={styles.cardTitle}>{item.title}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1E3A6E',
    padding: SIZES.padding * 1.5,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.82)',
    textAlign: 'center',
    marginBottom: 24,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  card: {
    width: '48%',
    marginBottom: 16,
  },
  cardImg: {
    width: '100%',
    height: 120,
    borderRadius: 10,
  },
  cardTitle: {
    fontSize: 13,
    fontWeight: '500',
    color: COLORS.white,
    marginTop: 8,
    textAlign: 'center',
  },
});