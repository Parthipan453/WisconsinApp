import React from 'react';
import { View, Text, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function ResearchHeroSection() {
  return (
    <View style={styles.container}>
      <ImageBackground
        source={require('../../assets/images/research_hero.jpg')}
        style={styles.banner}
        resizeMode="cover"
        imageStyle={styles.bannerImage}
      >
        <View style={styles.overlay}>
          <View style={styles.content}>
            <Text style={styles.title}>Research</Text>
            <View style={styles.redLine} />
            <Text style={styles.subtitle}>
              Explore ideas. Advancing knowledge.{'\n'}
              Creating impact
            </Text>
          </View>
        </View>
      </ImageBackground>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    padding: SIZES.padding,
  },
  banner: {
    height: 260,
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
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    paddingHorizontal: 24,
    borderRadius: 20,
  },
  content: {
    maxWidth: '90%',
  },
  title: {
    fontSize: 36,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  redLine: {
    width: 100,
    height: 5,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.white,
    lineHeight: 24,
  },
});