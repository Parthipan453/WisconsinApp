import React from 'react';
import { View, Text, ImageBackground, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function ResearchImpactSection() {
  return (
    <ImageBackground
      source={require('../../assets/images/bg_space.png')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.redLine} />
          <Text style={styles.title}>
            Research matters.{'\n'}
            Let us <Text style={styles.highlight}>protect it.</Text>
          </Text>
        </View>

        <Text style={styles.description}>
          Research at the University of Wisconsin–Madison drives innovation,
          saves lives, creates jobs, supports small businesses, and fuels the
          industries that keep America competitive and secure.
        </Text>

        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>
            Discover the impact of UW research
          </Text>
        </TouchableOpacity>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: 500,
    justifyContent: 'center',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 14,
    marginBottom: 20,
  },
  redLine: {
    width: 4,
    height: 60,
    backgroundColor: COLORS.navbarBg,
  },
  title: {
    flex: 1,
    fontSize: 26,
    fontWeight: '700',
    color: COLORS.white,
    lineHeight: 32,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  description: {
    fontSize: 14,
    color: COLORS.white,
    lineHeight: 22,
    marginBottom: 24,
  },
  button: {
    borderWidth: 2,
    borderColor: COLORS.white,
    borderRadius: 30,
    paddingVertical: 10,
    paddingHorizontal: 18,
    alignSelf: 'flex-start',
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
});