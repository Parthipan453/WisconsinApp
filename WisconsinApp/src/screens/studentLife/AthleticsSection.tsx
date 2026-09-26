import React from 'react';
import { View, Text, ImageBackground, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function AthleticsSection() {
  return (
    <ImageBackground
      source={require('../../assets/images/sports-img.jpg')}
      style={styles.container}
      resizeMode="cover"
      imageStyle={styles.bgImageStyle}
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <View style={styles.titleWrapper}>
          <View style={styles.redLine} />
          <Text style={styles.title}>
            Badgers are <Text style={styles.underline}>always</Text> on the move
          </Text>
        </View>
        <Text style={styles.description}>
          At UW–Madison, there's an activity for everyone: from NCAA events
          and club sports to pickup games at the Nick and Quidditch on the quad.
        </Text>
        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>Discover athletics at UW</Text>
        </TouchableOpacity>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    minHeight: 400,
    justifyContent: 'center',
    backgroundColor: '#000000',  // ← fallback
  },
  bgImageStyle: {
    resizeMode: 'cover',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.35)',
  },
  content: {
    padding: SIZES.padding * 2,
  },
  titleWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 14,
    marginBottom: 20,
  },
  redLine: {
    width: 5,
    height: 60,
    backgroundColor: COLORS.navbarBg,
  },
  title: {
    flex: 1,
    fontSize: 26,
    fontWeight: '600',
    color: COLORS.white,
    lineHeight: 32,
  },
  underline: {
    textDecorationLine: 'underline',
  },
  description: {
    fontSize: 15,
    lineHeight: 24,
    color: COLORS.white,
    marginBottom: 24,
  },
  button: {
    backgroundColor: COLORS.white,
    borderWidth: 2,
    borderColor: COLORS.navbarBg,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  buttonText: {
    color: '#111',
    fontSize: 14,
    fontWeight: '600',
  },
});