import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function ResearchStorySection() {
  return (
    <View style={styles.container}>
      <View style={styles.imageWrapper}>
        <View style={styles.redShape} />
        <Image
          source={require('../../assets/images/research_dr.jpg')}
          style={styles.image}
        />
      </View>

      <View style={styles.content}>
        <View style={styles.quoteRow}>
          <Text style={styles.quoteIcon}>❝</Text>
          <View style={styles.quoteLine} />
        </View>

        <Text style={styles.quote}>
          It has been really monumental for me to realize there are people
          who are really excited to help me get to where I want to go.
        </Text>

        <View style={styles.smallDivider} />

        <View style={styles.studentInfo}>
          <Text style={styles.studentText}>
            <Text style={styles.studentName}>Eryne Jenkins</Text>, a biology and
            environmental studies double major, conducts research in the
            Reproductive Endocrinology & Infertility Laboratory.
          </Text>
        </View>

        <TouchableOpacity style={styles.button}>
          <View style={styles.arrowCircle}>
            <Text style={styles.arrowText}>→</Text>
          </View>
          <Text style={styles.buttonText}>Read Eryne's story</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
    padding: SIZES.padding * 1.5,
  },
  imageWrapper: {
    position: 'relative',
    marginBottom: 30,
  },
  redShape: {
    position: 'absolute',
    left: -10,
    bottom: -15,
    width: '55%',
    height: '40%',
    backgroundColor: COLORS.navbarBg,
    zIndex: 1,
  },
  image: {
    width: '100%',
    height: 280,
    borderRadius: 12,
    zIndex: 2,
  },
  content: {
    paddingHorizontal: 6,
  },
  quoteRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  quoteIcon: {
    fontSize: 36,
    color: COLORS.navbarBg,
    fontWeight: 'bold',
  },
  quoteLine: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.navbarBg,
  },
  quote: {
    fontSize: 18,
    fontWeight: '400',
    color: '#111',
    lineHeight: 26,
    marginBottom: 18,
  },
  smallDivider: {
    width: 70,
    height: 1,
    backgroundColor: '#999',
    marginBottom: 16,
  },
  studentInfo: {
    borderLeftWidth: 3,
    borderLeftColor: COLORS.navbarBg,
    paddingLeft: 14,
    marginBottom: 22,
  },
  studentText: {
    fontSize: 14,
    color: '#111',
    lineHeight: 22,
  },
  studentName: {
    color: COLORS.navbarBg,
    fontWeight: '700',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  arrowCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 1,
    borderColor: '#777',
    justifyContent: 'center',
    alignItems: 'center',
  },
  arrowText: {
    color: COLORS.navbarBg,
    fontSize: 18,
    fontWeight: '700',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111',
  },
});