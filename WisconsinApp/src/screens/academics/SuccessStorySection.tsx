import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function SuccessStorySection() {
  return (
    <View style={styles.container}>
      <View style={styles.imageWrapper}>
        <View style={styles.redFrame} />
        <Image
          source={require('../../assets/images/doc.jpg')}
          style={styles.image}
        />
      </View>

      <View style={styles.content}>
        <Text style={styles.quoteIcon}>❝</Text>
        <Text style={styles.quoteText}>
          I feel like the faculty here really care about my future success.
          Everybody is willing to introduce me to their colleagues.
        </Text>

        <View style={styles.personInfo}>
          <Text style={styles.personText}>
            <Text style={styles.personName}>Julia Martien</Text>, recipient of the
            Jennifer L. Reed Bioenergy Science Award, is a scientist and graduate
            student in bacteriology.
          </Text>
        </View>

        <TouchableOpacity style={styles.learnMoreBtn}>
          <View style={styles.circleArrow}>
            <Text style={styles.arrowText}>→</Text>
          </View>
          <Text style={styles.learnMoreText}>Learn more about Julia</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    padding: SIZES.padding * 1.5,
  },
  imageWrapper: {
    position: 'relative',
    marginBottom: 40,
  },
  redFrame: {
    position: 'absolute',
    left: -15,
    bottom: -15,
    width: '60%',
    height: '60%',
    backgroundColor: COLORS.navbarBg,
    borderRadius: 8,
    zIndex: 1,
  },
  image: {
    width: '100%',
    height: 260,
    borderRadius: 12,
    zIndex: 2,
  },
  content: {
    paddingHorizontal: 6,
  },
  quoteIcon: {
    fontSize: 40,
    color: COLORS.navbarBg,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  quoteText: {
    fontSize: 18,
    fontWeight: '400',
    color: '#1A1A1A',
    lineHeight: 26,
    marginBottom: 20,
  },
  personInfo: {
    marginBottom: 20,
  },
  personText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 22,
  },
  personName: {
    color: COLORS.navbarBg,
    fontWeight: '700',
  },
  learnMoreBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  circleArrow: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.navbarBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  arrowText: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: '700',
  },
  learnMoreText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111',
  },
});