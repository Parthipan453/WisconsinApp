import React from 'react';
import { View, Text, ImageBackground, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function HeroSection({ navigation }: any) {
  return (
    <View style={styles.container}>
      <ImageBackground
        source={require('../../assets/images/hero4.png')}
        style={styles.hero}
        resizeMode="cover"
      >
        <View style={styles.overlay} />
        <View style={styles.content}>
          <Text style={styles.tagline}>Launch your future at UW</Text>
        </View>
      </ImageBackground>

      {/* CTA Bar - overlapping */}
      <View style={styles.ctaWrapper}>
        <View style={styles.ctaInner}>
          <TouchableOpacity style={styles.btn}>
            <Text style={styles.btnText}>Visit Campus</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.btn}>
            <Text style={styles.btnText}>Apply to UW</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.btn}>
            <Text style={styles.btnText}>Explore Majors</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 80,
  },
  hero: {
    width: '100%',
    height: 350,
    justifyContent: 'center',
    alignItems: 'center',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.35)',
  },
  content: {
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  tagline: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    textShadowColor: 'rgba(0,0,0,0.5)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 8,
  },
  ctaWrapper: {
    position: 'absolute',
    bottom: -60,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  ctaInner: {
    backgroundColor: COLORS.navbarBg,
    width: '85%',
    borderRadius: 15,
    paddingVertical: 24,
    paddingHorizontal: 16,
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 10,
  },
  btn: {
    borderWidth: 2,
    borderColor: COLORS.white,
    borderRadius: 10,
    backgroundColor: COLORS.white,
    paddingVertical: 10,
    paddingHorizontal: 18,
  },
  btnText: {
    color: COLORS.navbarBg,
    fontSize: 13,
    fontWeight: '700',
  },
});