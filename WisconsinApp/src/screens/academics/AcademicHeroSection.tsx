import React from 'react';
import { View, Text, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function AcademicHeroSection() {
  return (
    <ImageBackground
      source={require('../../assets/images/academicbuilding.png')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <Text style={styles.sectionTitle}>Academics</Text>
        <View style={styles.titleLine} />
        <Text style={styles.title}>
          Your path.{'\n'}Your purpose.
        </Text>
        <Text style={styles.subtitle}>
          A major for every passion, a degree for every dream
        </Text>
        <Text style={styles.description}>
          At UW–Madison you will find your fit. Our campus offers some 600
          undergraduate and graduate majors and more than 9,000 courses — from
          accounting to zoology and everything in between.
        </Text>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    minHeight: 500,
    justifyContent: 'center',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.6)',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  sectionTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 10,
  },
  titleLine: {
    width: 90,
    height: 5,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 24,
  },
  title: {
    fontSize: 36,
    fontWeight: '600',
    color: COLORS.white,
    lineHeight: 44,
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 16,
  },
  description: {
    fontSize: 15,
    color: COLORS.white,
    lineHeight: 22,
  },
});