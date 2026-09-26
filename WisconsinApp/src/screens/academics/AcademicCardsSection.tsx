import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const CARDS = [
  { id: 1, icon: '🎓', title: 'Majors & Certificates', description: 'Explore undergraduate majors, minors, certificates and more.', screen: 'Majors' },
  { id: 2, icon: '📚', title: 'Courses', description: 'Discover programs designed for your goals.', screen: 'Courses' },
  { id: 3, icon: '🏫', title: 'Schools & Colleges', description: 'Explore academic departments and schools.', screen: 'Schools' },
  { id: 4, icon: '🌍', title: 'Graduate Programs', description: 'Learn globally through international programs.', screen: 'Graduate' },
];

export default function AcademicCardsSection({ navigation }: any) {
  return (
    <View style={styles.container}>
      {CARDS.map((card) => (
        <TouchableOpacity
          key={card.id}
          style={styles.card}
          onPress={() => navigation.navigate(card.screen)}
        >
          <View style={styles.cardHeader}>
            <View style={styles.iconCircle}>
              <Text style={styles.iconText}>{card.icon}</Text>
            </View>
            <Text style={styles.cardTitle}>{card.title}</Text>
          </View>
          <Text style={styles.cardDescription}>{card.description}</Text>
          <Text style={styles.cardArrow}>→</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding,
    marginTop: -60,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 10,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 10,
    elevation: 5,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    marginBottom: 12,
  },
  iconCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 2,
    borderColor: COLORS.navbarBg,
    backgroundColor: 'rgba(197,5,12,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 22,
  },
  cardTitle: {
    flex: 1,
    fontSize: 17,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  cardDescription: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
    marginBottom: 10,
  },
  cardArrow: {
    fontSize: 22,
    color: COLORS.navbarBg,
    fontWeight: '700',
    alignSelf: 'flex-end',
  },
});