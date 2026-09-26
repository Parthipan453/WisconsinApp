import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const COMMUNITY_LINKS = [
  'Fraternity and Sorority Life',
  'Fraternity and Sorority Life',
  'Fraternity and Sorority Life',
  'Fraternity and Sorority Life',
];

function CommunityCard() {
  return (
    <View style={styles.card}>
      <View style={styles.iconCircle}>
        <Text style={styles.icon}>👥</Text>
      </View>
      <View style={styles.redLine} />
      <Text style={styles.title}>Find your community</Text>
      <Text style={styles.description}>
        UW–Madison welcomes students from all over the world and from every
        background. On a large campus, it is essential to build community.
      </Text>

      {COMMUNITY_LINKS.map((link, index) => (
        <View key={index} style={styles.linkRow}>
          <Text style={styles.linkText}>🏠 {link}</Text>
          <Text style={styles.arrowIcon}>→</Text>
        </View>
      ))}
    </View>
  );
}

export default function CommunitySection() {
  return (
    <View style={styles.container}>
      <CommunityCard />
      <CommunityCard />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding,
    backgroundColor: COLORS.white,
  },
  card: {
    backgroundColor: '#F8F8F8',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderBottomWidth: 4,
    borderBottomColor: COLORS.navbarBg,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 2,
    borderColor: COLORS.navbarBg,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  icon: {
    fontSize: 20,
  },
  redLine: {
    width: 40,
    height: 3,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 12,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 12,
  },
  description: {
    fontSize: 14,
    lineHeight: 22,
    color: '#333',
    marginBottom: 20,
  },
  linkRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#DDD',
  },
  linkText: {
    fontSize: 14,
    color: COLORS.text,
    flex: 1,
  },
  arrowIcon: {
    color: COLORS.navbarBg,
    fontSize: 18,
  },
});