import React from 'react';
import { View, Text, Image, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const SPACE_CARDS = [
  { id: 1, number: '01', image: require('../../assets/images/space-1.jpg'), label: 'Nicholas recreation center (The nick)' },
  { id: 2, number: '01', image: require('../../assets/images/space-2.jpg'), label: 'Nicholas recreation center (The nick)' },
  { id: 3, number: '01', image: require('../../assets/images/space-3.jpg'), label: 'Nicholas recreation center (The nick)' },
  { id: 4, number: '01', image: require('../../assets/images/space-4.jpg'), label: 'Nicholas recreation center (The nick)' },
];

export default function FitnessSection() {
  return (
    <View style={styles.container}>
      {/* Hero Section */}
      <View style={styles.hero}>
        <Image
          source={require('../../assets/images/fitness_hero.jpg')}
          style={styles.heroBg}
          resizeMode="cover"
        />
        <View style={styles.heroOverlay} />
        <View style={styles.heroContent}>
          <View style={styles.redBar} />
          <Text style={styles.heroTitle}>
            We believe in physical and{'\n'}
            <Text style={styles.highlight}>mental fitness</Text>
          </Text>
          <TouchableOpacity style={styles.heroButton}>
            <Text style={styles.heroButtonText}>
              Explore health and wellness program →
            </Text>
          </TouchableOpacity>
        </View>
        <Image
          source={require('../../assets/images/fit_logo.png')}
          style={styles.fitLogo}
        />
      </View>

      {/* Workout Section */}
      <View style={styles.workoutSection}>
        <View style={styles.redBar} />
        <Text style={styles.workoutTitle}>
          Sweat it out in our{'\n'}
          modern{' '}
          <Text style={styles.workoutHighlight}>workout spaces</Text>
        </Text>
        <View style={styles.horizontalLine} />
        <Text style={styles.workoutParagraph}>
          There's no shortage of modern amenities for the fitness-forward
          Badger: 30,000 square feet of brand-new workout space, an
          Olympic-size pool, indoor tennis courts and tracks, outdoor synthetic
          turf fields, a recreational ice rink, and much more.
        </Text>
        <Image
          source={require('../../assets/images/workout.jpg')}
          style={styles.workoutImage}
        />
      </View>

      {/* Explore Spaces Heading */}
      <View style={styles.headingRow}>
        <View style={styles.headingLine} />
        <Text style={styles.heading}>Explore our spaces</Text>
        <View style={styles.headingLine} />
      </View>

      {/* Space Cards */}
      <View style={styles.cardsGrid}>
        {SPACE_CARDS.map((card) => (
          <View key={card.id} style={styles.card}>
            <Image source={card.image} style={styles.cardImage} />
            <View style={styles.cardBody}>
              <View>
                <Text style={styles.cardNumber}>{card.number}</Text>
                <View style={styles.cardRedBar} />
              </View>
              <Text style={styles.cardLabel}>{card.label}</Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
  // Hero
  hero: {
    position: 'relative',
    minHeight: 400,
    justifyContent: 'center',
  },
  heroBg: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    width: '100%',
    height: '100%',
  },
  heroOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.2)',
  },
  heroContent: {
    paddingHorizontal: 24,
    paddingVertical: 40,
    maxWidth: '70%',
  },
  redBar: {
    width: 70,
    height: 6,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 20,
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
    lineHeight: 32,
    marginBottom: 20,
  },
  highlight: {
    color: COLORS.navbarBg,
    fontStyle: 'italic',
  },
  heroButton: {
    backgroundColor: COLORS.navbarBg,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 5,
    alignSelf: 'flex-start',
  },
  heroButtonText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '600',
  },
  fitLogo: {
    position: 'absolute',
    top: 30,
    right: 30,
    width: 100,
    height: 100,
    resizeMode: 'contain',
  },
  // Workout
  workoutSection: {
    padding: 24,
  },
  workoutTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111',
    lineHeight: 30,
    marginBottom: 16,
  },
  workoutHighlight: {
    color: COLORS.navbarBg,
  },
  horizontalLine: {
    width: '100%',
    height: 2,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 16,
  },
  workoutParagraph: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111',
    lineHeight: 22,
    marginBottom: 20,
  },
  workoutImage: {
    width: '100%',
    height: 240,
    borderRadius: 20,
  },
  // Heading
  headingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    marginVertical: 20,
    gap: 12,
  },
  headingLine: {
    flex: 1,
    height: 2,
    backgroundColor: COLORS.navbarBg,
  },
  heading: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.navbarBg,
  },
  // Cards
  cardsGrid: {
    paddingHorizontal: 16,
    paddingBottom: 30,
  },
  card: {
    marginBottom: 16,
  },
  cardImage: {
    width: '100%',
    height: 200,
    borderRadius: 10,
  },
  cardBody: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  cardNumber: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111',
    marginBottom: 6,
  },
  cardRedBar: {
    width: 27,
    height: 3,
    backgroundColor: COLORS.navbarBg,
  },
  cardLabel: {
    flex: 1,
    fontSize: 14,
    color: COLORS.navbarBg,
    fontWeight: '500',
    textAlign: 'right',
    marginLeft: 20,
  },
});