import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const SCHOOLS_1 = [
  '🏛️ School of Business',
  '📖 Law School',
  '❤️ School of Medicine and Public Health',
  '💊 School of Pharmacy',
  '🐛 School of Veterinary Medicine',
  '🔍 Search professional programs',
];

const SCHOOLS_2 = [
  '💼 Adult Career and Special Student Services',
  '🎒 Badger Precollege',
  '📚 Continuing Studies',
  '👥 Grandparents University',
  '🧭 The Odyssey Project',
  '💻 Online degree programs',
];

function ProSchoolCard({
  title,
  highlight,
  description,
  schools,
  showHelp,
}: {
  title: string;
  highlight: string;
  description: string;
  schools: string[];
  showHelp?: boolean;
}) {
  return (
    <View style={styles.card}>
      <Image
        source={require('../../assets/images/bucky_building.jpg')}
        style={styles.cardImage}
      />
      <View style={styles.cardContent}>
        <View style={styles.iconCircle}>
          <Text style={styles.iconText}>🎓</Text>
        </View>
        <View style={styles.line} />
        <Text style={styles.title}>
          {title}{'\n'}
          <Text style={styles.highlight}>{highlight}</Text>
        </Text>
        <Text style={styles.description}>{description}</Text>
      </View>

      {schools.map((school, index) => (
        <TouchableOpacity key={index} style={styles.linkRow}>
          <Text style={styles.linkText}>{school}</Text>
          <Text style={styles.linkArrow}>→</Text>
        </TouchableOpacity>
      ))}

      {showHelp && (
        <View style={styles.helpBox}>
          <Text style={styles.helpBold}>Not sure where to start?</Text>
          <Text style={styles.helpSmall}>
            Get help finding the right program for you →
          </Text>
        </View>
      )}
    </View>
  );
}

export default function ProSchoolsSection() {
  return (
    <View style={styles.container}>
      <ProSchoolCard
        title="Choose from our top-ranked"
        highlight="professional schools"
        description="UW-Madison's professional schools combine rigorous curricula with real-world experiences to jumpstart your career."
        schools={SCHOOLS_1}
      />
      <ProSchoolCard
        title="Join a community of lifelong"
        highlight="learners"
        description="Badgers never stop being curious. UW-Madison offers opportunities to help you grow as a professional and a person."
        schools={SCHOOLS_2}
        showHelp
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    padding: SIZES.padding,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 14,
    overflow: 'hidden',
    marginBottom: 20,
    borderBottomWidth: 5,
    borderBottomColor: COLORS.navbarBg,
  },
  cardImage: {
    width: '100%',
    height: 180,
    resizeMode: 'cover',
  },
  cardContent: {
    padding: 18,
  },
  iconCircle: {
    width: 46,
    height: 46,
    borderRadius: 23,
    borderWidth: 2,
    borderColor: COLORS.navbarBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 20,
  },
  line: {
    width: 40,
    height: 3,
    backgroundColor: COLORS.navbarBg,
    marginVertical: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1A1A1A',
    lineHeight: 26,
    marginBottom: 10,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  description: {
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
  },
  linkRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderTopWidth: 1,
    borderTopColor: '#DDD',
  },
  linkText: {
    fontSize: 14,
    color: '#1A1A1A',
    flex: 1,
  },
  linkArrow: {
    color: COLORS.navbarBg,
    fontSize: 18,
    fontWeight: '700',
  },
  helpBox: {
    margin: 18,
    padding: 12,
    backgroundColor: '#F8E5E5',
    borderRadius: 8,
  },
  helpBold: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  helpSmall: {
    fontSize: 12,
    color: COLORS.navbarBg,
  },
});