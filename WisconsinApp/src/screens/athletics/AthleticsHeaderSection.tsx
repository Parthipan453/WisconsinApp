import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function AthleticsHeaderSection() {
  return (
    <View style={styles.container}>
      <Image
        source={require('../../assets/images/ath_header.jpg')}
        style={styles.headerImage}
        resizeMode="cover"
      />
      <View style={styles.overlay}>
        <Text style={styles.headerText}>Athletics</Text>
        <View style={styles.redLine} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    height: 250,
  },
  headerImage: {
    width: '100%',
    height: '100%',
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
  },
  headerText: {
    color: COLORS.white,
    fontSize: 32,
    fontWeight: '700',
  },
  redLine: {
    width: 60,
    height: 4,
    backgroundColor: COLORS.navbarBg,
    marginTop: 8,
  },
});