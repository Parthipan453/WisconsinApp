import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const PROMISES = [
  {
    id: 1,
    title: 'Bucky\'s Tuition Promise',
    description: 'Free tuition for incoming Wisconsin resident students whose family\'s household adjusted gross income is $65,000 or less.',
    image: require('../../assets/images/bucky_building.jpg'),
  },
  {
    id: 2,
    title: 'Bucky\'s Pell Pathway',
    description: 'A commitment to meet the full financial need of incoming Wisconsin resident students who are eligible for the Federal Pell Grant.',
    image: require('../../assets/images/bucky_building_two.jpg'),
  },
  {
    id: 3,
    title: 'Wisconsin Tribal Educational Promise',
    description: 'A program to fund the full cost of attendance for Wisconsin resident students who are enrolled members of a federally recognized American Indian tribe.',
    image: require('../../assets/images/bucky_building.jpg'),
  },
  {
    id: 4,
    title: 'Badger Promise',
    description: 'Free tuition for first-generation college students who are Wisconsin residents and have transferred from a two-year UW Branch campus.',
    image: require('../../assets/images/bucky_building_two.jpg'),
  },
];

export default function PromiseSection() {
  return (
    <View style={styles.container}>
      <View style={styles.headingWrapper}>
        <View style={styles.redBar} />
        <Text style={styles.heading}>
          Our promise to{'\n'}
          <Text style={styles.highlight}>Wisconsin students</Text>
        </Text>
      </View>

      <Text style={styles.description}>
        UW-Madison is within your reach. That is our promise to all Wisconsin
        students, no matter their financial means. Nearly two-thirds of our
        students leave UW-Madison debt-free.
      </Text>

      {PROMISES.map((promise) => (
        <View key={promise.id} style={styles.card}>
          <View style={styles.redStrip} />
          <Image source={promise.image} style={styles.cardImage} />
          <View style={styles.cardContent}>
            <View style={styles.iconCircle}>
              <Text style={styles.iconText}>🎓</Text>
            </View>
            <Text style={styles.cardTitle}>{promise.title}</Text>
            <View style={styles.titleLine} />
            <Text style={styles.cardDescription}>{promise.description}</Text>
            <TouchableOpacity style={styles.programLink}>
              <View style={styles.arrowCircle}>
                <Text style={styles.arrowText}>→</Text>
              </View>
              <Text style={styles.programLinkText}>Program details</Text>
            </TouchableOpacity>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    padding: SIZES.padding * 1.5,
  },
  headingWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 16,
  },
  redBar: {
    width: 5,
    height: 60,
    backgroundColor: COLORS.navbarBg,
  },
  heading: {
    flex: 1,
    fontSize: 24,
    fontWeight: '600',
    color: '#1A1A1A',
    lineHeight: 30,
  },
  highlight: {
    color: COLORS.navbarBg,
    fontWeight: '700',
  },
  description: {
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
    marginBottom: 24,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 10,
    overflow: 'hidden',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  redStrip: {
    height: 8,
    backgroundColor: COLORS.navbarBg,
  },
  cardImage: {
    width: '100%',
    height: 180,
    resizeMode: 'cover',
  },
  cardContent: {
    padding: 20,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#F7E4E4',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconText: {
    fontSize: 22,
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 10,
  },
  titleLine: {
    width: 60,
    height: 4,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 14,
  },
  cardDescription: {
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
    marginBottom: 16,
  },
  programLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  arrowCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
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
  programLinkText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1A1A1A',
  },
});