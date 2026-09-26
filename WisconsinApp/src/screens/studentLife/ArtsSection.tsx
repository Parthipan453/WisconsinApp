import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function ArtsSection() {
  return (
    <View style={styles.container}>
      <View style={styles.redLine} />
      <Text style={styles.title}>
        We are an arts destination drawing{' '}
        <Text style={styles.highlight}>national attention</Text>
      </Text>
      <Text style={styles.description}>
        You can feel the creativity in the air. Within a few campus blocks lie
        the largest museum collection in the Big Ten, a 650-seat concert hall,
        and several performance spaces serving up student productions.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding * 1.5,
    backgroundColor: '#F8F8F8',
  },
  redLine: {
    width: 50,
    height: 4,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '600',
    color: COLORS.text,
    lineHeight: 28,
    marginBottom: 14,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  description: {
    fontSize: 15,
    lineHeight: 24,
    color: '#333',
  },
});