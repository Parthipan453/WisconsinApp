import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function BannerSection() {
  return (
    <View style={styles.container}>
      {/* Banner with image + overlay */}
      <View style={styles.bannerWrapper}>
        <View style={styles.banner}>
          <Image
            source={require('../../assets/images/student_lifestyle.jpg')}
            style={styles.bannerImage}
            resizeMode="cover"
          />
          <View style={styles.overlay}>
            <View style={styles.content}>
              <Text style={styles.title}>Students Life</Text>
              <View style={styles.redLine} />
              <Text style={styles.subtitle}>
                At UW-Madison, life is about more than what you learn —
                it's about who you become and the community you build.
              </Text>
            </View>
          </View>
        </View>
      </View>

      {/* Text section below banner */}
      <View style={styles.textSection}>
        <Text style={styles.heading}>
          Badgers work hard and play hard. After class, our students build
          community and stay active through a wide variety of clubs,
          organizations, and campus events.
        </Text>

        {/* Center line with circle */}
        <View style={styles.centerLine}>
          <View style={styles.circle} />
        </View>

        {/* Button */}
        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>Explore the student experience</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    paddingVertical: 20,
  },
  bannerWrapper: {
    paddingHorizontal: SIZES.padding,
    marginBottom: 24,
  },
  banner: {
    height: 280,
    borderRadius: 20,
    overflow: 'hidden',
    position: 'relative',
  },
  bannerImage: {
    width: '100%',
    height: '100%',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  content: {
    maxWidth: '90%',
  },
  title: {
    fontSize: 36,
    fontWeight: '900',
    color: COLORS.white,
    marginBottom: 12,
  },
  redLine: {
    width: 80,
    height: 5,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 15,
    color: COLORS.white,
    lineHeight: 22,
  },
  textSection: {
    paddingHorizontal: SIZES.padding,
    alignItems: 'center',
  },
  heading: {
    fontSize: 15,
    lineHeight: 24,
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 20,
  },
  centerLine: {
    width: '100%',
    height: 1,
    backgroundColor: '#CCCCCC',
    marginVertical: 16,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  circle: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: COLORS.navbarBg,
    position: 'absolute',
  },
  button: {
    borderWidth: 2,
    borderColor: COLORS.navbarBg,
    borderRadius: 25,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: COLORS.white,
    marginTop: 8,
  },
  buttonText: {
    color: COLORS.navbarBg,
    fontSize: 14,
    fontWeight: '600',
  },
});