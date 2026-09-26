import React from 'react';
import { View, Text, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../../constants/colors';

export default function MajorsBannerSection() {
  return (
    <ImageBackground
      source={require('../../../assets/images/academicbg.jpg')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <Text style={styles.title}>Academics</Text>
        <View style={styles.redLine} />
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    height: 200,
    justifyContent: 'flex-end',
    paddingBottom: 30,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  content: {
    alignItems: 'center',
  },
  title: {
    color: COLORS.white,
    fontSize: 32,
    fontWeight: '600',
    marginBottom: 12,
    fontFamily: 'serif',
  },
  redLine: {
    width: 80,
    height: 4,
    backgroundColor: COLORS.navbarBg,
  },
});