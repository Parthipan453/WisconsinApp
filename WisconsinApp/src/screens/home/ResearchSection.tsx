import React from 'react';
import { View, Text, ImageBackground, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function ResearchSection() {
  return (
    <ImageBackground
      source={require('../../assets/images/research.png')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <Text style={styles.title}>
          Our research solves mysteries and transforms lives
        </Text>
        <Text style={styles.description}>
          UW-Madison is one of the 10 largest research institutions in the country,
          allocating more than $1 billion annually to groundbreaking exploration.
        </Text>

        <TouchableOpacity style={styles.btn}>
          <Text style={styles.btnText}>Research at UW-Madison</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.btn}>
          <Text style={styles.btnText}>Research benefiting Wisconsin</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.btn}>
          <Text style={styles.btnText}>Why protecting research matters</Text>
        </TouchableOpacity>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    minHeight: 450,
    justifyContent: 'center',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(10,20,60,0.65)',
  },
  content: {
    padding: SIZES.padding * 2,
  },
  title: {
    fontSize: 26,
    fontWeight: '600',
    color: COLORS.white,
    lineHeight: 32,
    marginBottom: 16,
  },
  description: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.92)',
    lineHeight: 24,
    marginBottom: 24,
  },
  btn: {
    borderWidth: 2,
    borderColor: COLORS.white,
    borderRadius: 6,
    paddingVertical: 10,
    paddingHorizontal: 16,
    marginBottom: 10,
    alignSelf: 'flex-start',
  },
  btnText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
});