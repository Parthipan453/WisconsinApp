import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function PurposeSection() {
  return (
    <View style={styles.container}>
      {/* Header with logo + lines */}
      <View style={styles.headerRow}>
        <View style={styles.line} />
        <Image source={require('../../assets/images/wisconsin-logo-png.png')} style={styles.logo} />
        <View style={styles.line} />
      </View>

      <Text style={styles.eyebrow}>Our purpose</Text>

      {/* Image */}
      <Image source={require('../../assets/images/public.jpg')} style={styles.image} />

      {/* Content */}
      <Text style={styles.title}>
        We are a public university guided by{' '}
        <Text style={styles.highlight}>public service</Text>
      </Text>

      <Text style={styles.description}>
        UW–Madison's longest and proudest tradition is the Wisconsin Idea:
        the principle that our work should improve people's lives beyond
        the boundaries of campus.
      </Text>

      <TouchableOpacity style={styles.link}>
        <View style={styles.iconCircle}>
          <Text style={styles.arrow}>→</Text>
        </View>
        <Text style={styles.linkText}>Learn more about the Wisconsin</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding * 1.5,
    marginBottom: 40,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  line: {
    flex: 1,
    height: 1.5,
    backgroundColor: '#D0D0D0',
  },
  logo: {
    width: 60,
    height: 40,
    marginHorizontal: 12,
    resizeMode: 'contain',
  },
  eyebrow: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.navbarBg,
    textAlign: 'center',
    marginBottom: 24,
  },
  image: {
    width: '100%',
    height: 220,
    borderRadius: 12,
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: '#1A1A1A',
    lineHeight: 30,
    marginBottom: 14,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  description: {
    fontSize: 15,
    color: '#333',
    lineHeight: 24,
    marginBottom: 20,
  },
  link: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#1A1A1A',
    justifyContent: 'center',
    alignItems: 'center',
  },
  arrow: {
    fontSize: 16,
    color: '#1A1A1A',
    fontWeight: '700',
  },
  linkText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1A1A',
  },
});