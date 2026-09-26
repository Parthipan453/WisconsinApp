import React from 'react';
import { View, Text, ImageBackground, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function MadisonSection() {
  return (
    <ImageBackground
      source={require('../../assets/images/madison_bg.png')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <View style={styles.titleWrapper}>
          <View style={styles.redBar} />
          <Text style={styles.title}>Madison, WI :</Text>
        </View>
        <Text style={styles.subtitle}>The ultimate college town</Text>
        <Text style={styles.description}>
          This is where big-city opportunities meet small-town conveniences.
        </Text>

        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>Tour campus virtually</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>Explore Madison in every season</Text>
        </TouchableOpacity>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: 400,
    justifyContent: 'center',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  titleWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  redBar: {
    width: 5,
    height: 50,
    backgroundColor: COLORS.navbarBg,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: COLORS.white,
  },
  subtitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  description: {
    fontSize: 16,
    color: COLORS.white,
    lineHeight: 24,
    marginBottom: 24,
  },
  button: {
    borderWidth: 2,
    borderColor: COLORS.white,
    borderRadius: 6,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 10,
    alignItems: 'center',
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 15,
    fontWeight: '600',
  },
});