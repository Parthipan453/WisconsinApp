import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function StatewideSection() {
  return (
    <View style={styles.container}>
      <View style={styles.tagRow}>
        <View style={styles.tagLine} />
        <Text style={styles.tag}>TOGETHER, WE'RE STRONGER</Text>
      </View>

      <Text style={styles.title}>
        Our statewide{'\n'}
        <Text style={styles.highlight}>connection</Text>
      </Text>

      <View style={styles.divider}>
        <View style={styles.dividerLine} />
        <Image
          source={require('../../assets/images/logo.png')}
          style={styles.dividerLogo}
        />
        <View style={styles.dividerLine} />
      </View>

      <Text style={styles.description}>
        The University of Wisconsin–Madison is part of the Universities of
        Wisconsin. The system comprises 13 universities around the state.
        The Universities of Wisconsin serve more than 164,400 students with
        840-plus programs.
      </Text>

      <TouchableOpacity style={styles.button}>
        <View style={styles.arrowCircle}>
          <Text style={styles.arrowText}>→</Text>
        </View>
        <Text style={styles.buttonText}>
          Learn about the Universities of Wisconsin
        </Text>
      </TouchableOpacity>

      <Image
        source={require('../../assets/images/mapabout.png')}
        style={styles.map}
        resizeMode="contain"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding * 1.5,
    backgroundColor: '#F8F8F8',
  },
  tagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  tagLine: {
    width: 40,
    height: 4,
    backgroundColor: COLORS.navbarBg,
  },
  tag: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.navbarBg,
    letterSpacing: 1,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#111',
    lineHeight: 32,
    marginBottom: 16,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 10,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#CCC',
  },
  dividerLogo: {
    width: 30,
    height: 20,
    resizeMode: 'contain',
  },
  description: {
    fontSize: 15,
    color: '#666',
    lineHeight: 22,
    marginBottom: 24,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    marginBottom: 30,
  },
  arrowCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.navbarBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  arrowText: {
    color: COLORS.white,
    fontSize: 20,
    fontWeight: '700',
  },
  buttonText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#111',
    textDecorationLine: 'underline',
  },
  map: {
    width: '100%',
    height: 280,
  },
});