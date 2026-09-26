import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function MilestoneSection() {
  return (
    <View style={styles.container}>
      <View style={styles.tagRow}>
        <View style={styles.tagLine} />
        <Text style={styles.tag}>OUR PAST. OUR PURPOSE.</Text>
      </View>

      <Text style={styles.title}>
        Our <Text style={styles.highlight}>milestones</Text>
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
        At UW-Madison, we drive change by pushing beyond boundaries. From
        life-saving medical advances to barrier-breaking social movements,
        our campus continues to be home to history in the making.
      </Text>

      <TouchableOpacity style={styles.button}>
        <View style={styles.arrowCircle}>
          <Text style={styles.arrowText}>→</Text>
        </View>
        <Text style={styles.buttonText}>
          Timeline: Explore UW over the years
        </Text>
      </TouchableOpacity>

      <View style={styles.imageWrapper}>
        <Image
          source={require('../../assets/images/oldphoto.png')}
          style={styles.image}
        />
        <View style={styles.yearBadge}>
          <Text style={styles.yearText}>1848</Text>
          <Text style={styles.yearSub}>WISCONSIN MADISON</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding * 1.5,
    backgroundColor: '#F5F5F5',
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
    fontSize: 28,
    fontWeight: '600',
    color: '#111',
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
  imageWrapper: {
    position: 'relative',
  },
  image: {
    width: '100%',
    height: 280,
    borderRadius: 20,
  },
  yearBadge: {
    position: 'absolute',
    bottom: -20,
    right: -10,
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#D7C2A0',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 6,
  },
  yearText: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.navbarBg,
  },
  yearSub: {
    fontSize: 8,
    fontWeight: '700',
    color: '#111',
    marginTop: 2,
  },
});