import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const LINKS = [
  { id: 1, icon: '🎓', text: 'Undergraduate majors and certificates' },
  { id: 2, icon: '🎓', text: 'Undergraduate majors and certificates' },
  { id: 3, icon: '🎓', text: 'Undergraduate majors and certificates' },
];

export default function DiscoverySection() {
  return (
    <View style={styles.container}>
      <View style={styles.redLine} />
      <Text style={styles.title}>
        Your path to{'\n'}
        discovery <Text style={styles.highlight}>starts here</Text>
      </Text>
      <Text style={styles.description}>
        UW–Madison is distinct for its breadth of disciplines and cross-campus
        research collaborations. Hands-on research opportunities abound for
        undergraduate students and span the social sciences, medicine,
        humanities, and STEM fields.
      </Text>

      <Image
        source={require('../../assets/images/research_about.jpg')}
        style={styles.image}
      />

      {LINKS.map((link) => (
        <TouchableOpacity key={link.id} style={styles.link}>
          <View style={styles.linkIcon}>
            <Text style={styles.linkIconText}>{link.icon}</Text>
          </View>
          <Text style={styles.linkText}>{link.text}</Text>
          <Text style={styles.linkArrow}>→</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F4F4F4',
    padding: SIZES.padding * 1.5,
  },
  redLine: {
    width: 48,
    height: 4,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 18,
  },
  title: {
    fontSize: 30,
    fontWeight: '700',
    color: '#111',
    lineHeight: 36,
    marginBottom: 20,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  description: {
    fontSize: 15,
    color: '#111',
    lineHeight: 22,
    marginBottom: 24,
  },
  image: {
    width: '100%',
    height: 220,
    borderRadius: 12,
    marginBottom: 24,
  },
  link: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: 'rgba(185,185,185,0.72)',
    borderRadius: 12,
    padding: 18,
    marginBottom: 12,
  },
  linkIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.navbarBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  linkIconText: {
    fontSize: 20,
  },
  linkText: {
    flex: 1,
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
    lineHeight: 20,
  },
  linkArrow: {
    color: COLORS.navbarBg,
    fontSize: 22,
    fontWeight: '700',
  },
});