import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const INFO_CARDS = [
  { id: 1, icon: '💰', title: 'Cost of attendance', description: 'Estimate the total cost of attending UW-Madison and plan ahead.' },
  { id: 2, icon: '💰', title: 'Cost of attendance', description: 'Estimate the total cost of attending UW-Madison and plan ahead.' },
  { id: 3, icon: '💰', title: 'Cost of attendance', description: 'Estimate the total cost of attending UW-Madison and plan ahead.' },
];

export default function TuitionSection() {
  return (
    <View style={styles.container}>
      {/* <ImageBackground
        source={require('../../assets/images/student_bg.jpg')}
        style={styles.background}
        resizeMode="cover"
      >
        <View style={styles.overlay} />
        <View style={styles.content}>
          <Image source={require('../../assets/images/student.jpg')} style={styles.studentImage} />

          <View style={styles.testimonial}>
            <View style={styles.quoteIcon}>
              <Text style={styles.quoteText}>❝</Text>
            </View>
            <Text style={styles.quote}>
              Bucky's Tuition Promise alleviated so many financial burdens.
              The idea of being able to focus solely on school during the
              academic year was huge.
            </Text>
            <View style={styles.redLine} />
            <Text style={styles.name}>Mackenzie Straub,</Text>
            <Text style={styles.description}>
              a UW alumna and recipient of Bucky's Tuition Promise, earned
              her degree in early childhood education.
            </Text>
            <TouchableOpacity style={styles.link}>
              <View style={styles.arrowCircle}>
                <Text style={styles.arrowText}>→</Text>
              </View>
              <Text style={styles.linkText}>Read Mackenzie's story</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ImageBackground> */}

      {INFO_CARDS.map((card) => (
        <View key={card.id} style={styles.infoCard}>
          <View style={styles.infoHeader}>
            <View style={styles.infoIconCircle}>
              <Text style={styles.infoIconText}>{card.icon}</Text>
            </View>
            <View style={styles.infoTitleArea}>
              <Text style={styles.infoTitle}>{card.title}</Text>
              <View style={styles.infoLine} />
            </View>
          </View>
          <Text style={styles.infoDescription}>{card.description}</Text>
          <Text style={styles.infoArrow}>→</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    padding: SIZES.padding,
  },
  background: {
    borderRadius: 12,
    overflow: 'hidden',
    padding: 20,
    marginBottom: 20,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255,255,255,0.75)',
  },
  content: {
    padding: 12,
  },
  studentImage: {
    width: '100%',
    height: 220,
    borderRadius: 12,
    marginBottom: 20,
  },
  testimonial: {
    paddingHorizontal: 8,
  },
  quoteIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.navbarBg,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  quoteText: {
    color: COLORS.white,
    fontSize: 28,
    fontWeight: 'bold',
    lineHeight: 30,
  },
  quote: {
    fontSize: 20,
    fontWeight: '500',
    color: '#1A1A1A',
    lineHeight: 28,
    marginBottom: 16,
  },
  redLine: {
    width: 50,
    height: 4,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 12,
  },
  name: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.navbarBg,
    marginBottom: 4,
  },
  description: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
    marginBottom: 16,
  },
  link: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  arrowCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: COLORS.navbarBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  arrowText: {
    color: COLORS.navbarBg,
    fontSize: 16,
    fontWeight: '700',
  },
  linkText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  infoCard: {
    backgroundColor: COLORS.white,
    borderRadius: 8,
    padding: 18,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  infoHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 12,
  },
  infoIconCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#F6E3E3',
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoIconText: {
    fontSize: 22,
  },
  infoTitleArea: {
    flex: 1,
    paddingTop: 6,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  infoLine: {
    width: 40,
    height: 3,
    backgroundColor: COLORS.navbarBg,
    marginTop: 8,
  },
  infoDescription: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  infoArrow: {
    position: 'absolute',
    right: 16,
    bottom: 14,
    color: COLORS.navbarBg,
    fontSize: 20,
    fontWeight: '700',
  },
});