import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function ResearchIntroSection() {
  return (
    <View style={styles.container}>
      {/* Divider with icon */}
      <View style={styles.divider}>
        <View style={styles.dividerLine} />
        <View style={styles.dividerIcon}>
          <Text style={styles.iconText}>🔀</Text>
        </View>
        <View style={styles.dividerLine} />
      </View>

      <Text style={styles.description}>
        As a leading research institution, we encourage creative and analytical
        inquiry. UW–Madison provides students opportunities to work alongside
        world-renowned scholars in pursuit of groundbreaking research with the
        potential to change lives.
      </Text>

      <TouchableOpacity style={styles.button}>
        <Text style={styles.buttonText}>Explore resources for researchers</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    paddingHorizontal: SIZES.padding * 1.5,
    paddingVertical: 40,
    alignItems: 'center',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    width: '100%',
    justifyContent: 'center',
  },
  dividerLine: {
    flex: 1,
    maxWidth: 100,
    height: 1,
    backgroundColor: '#CFCFCF',
  },
  dividerIcon: {
    width: 55,
    height: 55,
    borderRadius: 28,
    backgroundColor: '#F8E6E6',
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 16,
  },
  iconText: {
    fontSize: 22,
  },
  description: {
    fontSize: 16,
    lineHeight: 24,
    color: '#111',
    textAlign: 'center',
    marginBottom: 24,
    maxWidth: 600,
  },
  button: {
    borderWidth: 2,
    borderColor: COLORS.navbarBg,
    borderRadius: 25,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  buttonText: {
    color: COLORS.navbarBg,
    fontSize: 15,
    fontWeight: '600',
    textAlign: 'center',
  },
});