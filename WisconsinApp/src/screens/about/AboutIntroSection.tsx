import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function AboutIntroSection() {
  return (
    <View style={styles.container}>
      <Text style={styles.description}>
        Since its founding in 1848, this campus has been a catalyst for the
        extraordinary. As a public land-grant university and major research
        institution, our students, staff, and faculty engage in a world-class
        education while solving real-world problems. With public service — or
        as we call it,{' '}
        <Text style={styles.highlight}>The Wisconsin Idea</Text> — as our
        guiding principle, Badgers are creating a better future for everyone.
      </Text>

      <TouchableOpacity style={styles.buttonFilled}>
        <Text style={styles.buttonFilledText}>🏆 Meet our leadership</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.buttonOutline}>
        <Text style={styles.buttonOutlineText}>🎖️ Read our strategic framework</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding * 1.5,
    backgroundColor: COLORS.white,
  },
  description: {
    fontSize: 16,
    lineHeight: 24,
    color: '#151515',
    textAlign: 'center',
    marginBottom: 30,
  },
  highlight: {
    color: COLORS.navbarBg,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  buttonFilled: {
    backgroundColor: COLORS.navbarBg,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 20,
    marginBottom: 12,
    alignItems: 'center',
  },
  buttonFilledText: {
    color: COLORS.white,
    fontSize: 15,
    fontWeight: '600',
  },
  buttonOutline: {
    borderWidth: 2,
    borderColor: COLORS.navbarBg,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  buttonOutlineText: {
    color: COLORS.navbarBg,
    fontSize: 15,
    fontWeight: '600',
  },
});