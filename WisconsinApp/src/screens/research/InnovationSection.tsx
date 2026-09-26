import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function InnovationSection() {
  return (
    <View style={styles.container}>
      <Image
        source={require('../../assets/images/innovation_city.png')}
        style={styles.image}
      />
      <View style={styles.content}>
        <View style={styles.redLine} />
        <Text style={styles.title}>
          We help researchers become <Text style={styles.highlight}>innovators</Text>
        </Text>
        <Text style={styles.description}>
          Our entrepreneurial campus is its own Silicon Valley. We help our
          scientists and scholars navigate every step of the commercial path
          from discovery to market.
        </Text>
        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>
            Transform your research into products and services →
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
  },
  image: {
    width: '100%',
    height: 280,
    resizeMode: 'cover',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  redLine: {
    width: 46,
    height: 4,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 20,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111',
    lineHeight: 28,
    marginBottom: 16,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  description: {
    fontSize: 14,
    color: '#222',
    lineHeight: 22,
    marginBottom: 20,
  },
  button: {
    backgroundColor: COLORS.navbarBg,
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '600',
  },
});