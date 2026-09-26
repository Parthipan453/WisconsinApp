import React from 'react';
import { View, Text, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function AboutHeroSection() {
  return (
    <View style={styles.container}>
      <ImageBackground
        source={require('../../assets/images/about_home.jpg')}
        style={styles.banner}
        resizeMode="cover"
        imageStyle={styles.bannerImage}
      >
        <View style={styles.overlay}>
          <View style={styles.content}>
            <Text style={styles.title}>About UW-Madison</Text>
            <View style={styles.redLine} />
            <Text style={styles.subtitle}>
              A premier public, land-grant{'\n'}
              research university founded in 1848
            </Text>
          </View>
        </View>
      </ImageBackground>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding,
    backgroundColor: '#F5F5F5',
  },
  banner: {
    minHeight: 300,
    borderRadius: 20,
    overflow: 'hidden',
    justifyContent: 'center',
  },
  bannerImage: {
    borderRadius: 20,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.55)',
    justifyContent: 'center',
    paddingHorizontal: 24,
    borderRadius: 20,
  },
  content: {
    maxWidth: '90%',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  redLine: {
    width: 100,
    height: 6,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.white,
    lineHeight: 24,
  },
});