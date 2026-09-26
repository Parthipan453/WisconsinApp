import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const STATS = [
  { id: 1, number: '275', label: 'Study abroad programs' },
  { id: 2, number: '275', label: 'Study abroad programs' },
  { id: 3, number: '275', label: 'Study abroad programs' },
  { id: 4, number: '275', label: 'Study abroad programs' },
];

export default function TestimonialSection() {
  return (
    <View style={styles.container}>
      <Image
        source={require('../../assets/images/tree.png')}
        style={styles.bgImage}
        resizeMode="cover"
      />
      <View style={styles.overlay} />

      <View style={styles.content}>
        <Text style={styles.quoteMark}>"</Text>
        <Text style={styles.quoteText}>
          UW stood out to me because it is such a well-rounded university.
          There is a balance between nature and city life.
        </Text>
        <View style={styles.redLine} />
        <Text style={styles.author}>
          <Text style={styles.authorName}>Anna Staresinic</Text>, a UW alumna
          who majored in Information Science.
        </Text>

        <View style={styles.statsRow}>
          {STATS.map((stat) => (
            <View key={stat.id} style={styles.statCard}>
              <Text style={styles.statNumber}>{stat.number}</Text>
              <View style={styles.smallLine} />
              <Text style={styles.statLabel}>{stat.label}</Text>
            </View>
          ))}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    paddingVertical: 50,
    minHeight: 500,
  },
  bgImage: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255,255,255,0.75)',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  quoteMark: {
    fontSize: 50,
    color: COLORS.navbarBg,
    fontWeight: 'bold',
    lineHeight: 50,
    marginBottom: 8,
  },
  quoteText: {
    fontSize: 22,
    fontWeight: '500',
    color: COLORS.text,
    lineHeight: 30,
    marginBottom: 20,
  },
  redLine: {
    width: 60,
    height: 4,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 16,
  },
  author: {
    fontSize: 14,
    lineHeight: 22,
    color: '#333',
    marginBottom: 32,
  },
  authorName: {
    color: COLORS.navbarBg,
    fontWeight: '700',
  },
  statsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: 'rgba(236, 231, 231, 0.6)',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  statNumber: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.navbarBg,
  },
  smallLine: {
    width: 30,
    height: 2,
    backgroundColor: COLORS.navbarBg,
    marginVertical: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#555',
    textAlign: 'center',
  },
});