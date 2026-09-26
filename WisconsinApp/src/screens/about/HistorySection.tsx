import React from 'react';
import { View, Text, TouchableOpacity, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function HistorySection() {
  return (
    <ImageBackground
      source={require('../../assets/images/aboutbgimage.png')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <View style={styles.borderLeft}>
          <Text style={styles.title}>
            Finding truth in{'\n'}
            <Text style={styles.highlight}>our history</Text>
          </Text>
        </View>

        <View style={styles.greyBorder}>
          <Text style={styles.description}>
            UW-Madison is dedicated to creating a welcoming and inclusive
            community for people from every background. And we recognize
            that to create a better future, we must confront difficult
            parts of our past.
          </Text>

          <TouchableOpacity style={styles.buttonFilled}>
            <Text style={styles.buttonFilledText}>
              Center for Campus History →
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.buttonOutline}>
            <Text style={styles.buttonOutlineText}>
              Our Shared Future →
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: 500,
    paddingVertical: 50,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.45)',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  borderLeft: {
    borderLeftWidth: 3,
    borderLeftColor: COLORS.navbarBg,
    paddingLeft: 20,
    marginBottom: 30,
  },
  title: {
    fontSize: 28,
    fontWeight: '600',
    color: COLORS.white,
    lineHeight: 36,
  },
  highlight: {
    color: COLORS.navbarBg,
    fontStyle: 'italic',
  },
  greyBorder: {
    borderLeftWidth: 3,
    borderLeftColor: '#767272',
    paddingLeft: 20,
  },
  description: {
    fontSize: 16,
    color: COLORS.white,
    lineHeight: 24,
    marginBottom: 24,
  },
  buttonFilled: {
    backgroundColor: COLORS.navbarBg,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginBottom: 12,
    alignItems: 'center',
  },
  buttonFilledText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  buttonOutline: {
    borderWidth: 2,
    borderColor: COLORS.white,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonOutlineText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
});