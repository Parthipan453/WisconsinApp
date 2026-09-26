import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const LEARNING_CARDS = [
  { id: 1, number: '01', icon: '📖', title: 'Intellectual and personal growth', description: 'The Wisconsin Experience is our vision to create thoughtful, well-rounded citizens.' },
  { id: 2, number: '02', icon: '👥', title: 'Tight-knit communities', description: 'First-Year Interest Groups are small learning communities that provide an immersive experience.' },
  { id: 3, number: '03', icon: '💡', title: 'A Global Education', description: 'Our life-changing study abroad programs span some 60 countries and six continents.' },
];

export default function LearningSection() {
  return (
    <View style={styles.container}>
      <View style={styles.headingLine} />
      <Text style={styles.heading}>
        Active, collaborative, reflective:{'\n'}
        learning, <Text style={styles.highlight}>the UW way</Text>
      </Text>
      <Text style={styles.subheading}>
        At UW-Madison, learning happens everywhere - in the classroom, in our
        communities and around the world.
      </Text>

      {LEARNING_CARDS.map((card) => (
        <View key={card.id} style={styles.card}>
          <Image
            source={require('../../assets/images/thirdimage.jpg')}
            style={styles.cardImage}
          />
          <View style={styles.cardBody}>
            <View style={styles.cardTop}>
              <Text style={styles.cardNumber}>{card.number}</Text>
              <View style={styles.iconCircle}>
                <Text style={styles.iconText}>{card.icon}</Text>
              </View>
            </View>
            <Text style={styles.cardTitle}>{card.title}</Text>
            <Text style={styles.cardDescription}>{card.description}</Text>
            <Text style={styles.cardLink}>Learn about the Wisconsin Experience →</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F8F8F8',
    padding: SIZES.padding * 1.5,
  },
  headingLine: {
    width: 70,
    height: 6,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 20,
  },
  heading: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1A1A1A',
    lineHeight: 30,
    marginBottom: 14,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  subheading: {
    fontSize: 15,
    color: '#4A4A4A',
    lineHeight: 22,
    marginBottom: 24,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 20,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 4,
  },
  cardImage: {
    width: '100%',
    height: 180,
    borderRadius: 10,
    marginBottom: 16,
  },
  cardBody: {
    paddingHorizontal: 6,
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardNumber: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.navbarBg,
    textDecorationLine: 'underline',
  },
  iconCircle: {
    width: 55,
    height: 55,
    borderRadius: 28,
    backgroundColor: '#F8E6E6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 24,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 12,
  },
  cardDescription: {
    fontSize: 14,
    color: '#555',
    lineHeight: 22,
    marginBottom: 12,
  },
  cardLink: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.navbarBg,
  },
});