import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const LINKS = [
  { id: 1, icon: '👥', text: 'UW in the community' },
  { id: 2, icon: '👥', text: 'Wisconsin outreach' },
  { id: 3, icon: '👥', text: 'Public service programs' },
];

export default function WisconsinIdeaSection() {
  return (
    <View style={styles.container}>
      <Text style={styles.tag}>THE WISCONSIN IDEA</Text>
      <Text style={styles.title}>
        Our commitment to public service{'\n'}
        <Text style={styles.highlight}>regionally</Text>
      </Text>
      <View style={styles.redLine} />
      <Text style={styles.description}>
        Through teaching, research, and outreach, we partner with communities
        across Wisconsin to improve lives and build a better future for all.
      </Text>

      {LINKS.map((link) => (
        <TouchableOpacity key={link.id} style={styles.link}>
          <View style={styles.linkIcon}>
            <Text style={styles.linkIconText}>{link.icon}</Text>
          </View>
          <Text style={styles.linkText}>{link.text}</Text>
          <Text style={styles.linkArrow}>→</Text>
        </TouchableOpacity>
      ))}

      <Image
        source={require('../../assets/images/aboutvillage.jpg')}
        style={styles.image}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding * 1.5,
    backgroundColor: '#F8F8F8',
  },
  tag: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.navbarBg,
    letterSpacing: 1,
    marginBottom: 12,
  },
  title: {
    fontSize: 26,
    fontWeight: '600',
    color: '#000',
    lineHeight: 32,
    marginBottom: 12,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  redLine: {
    width: 70,
    height: 4,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 16,
  },
  description: {
    fontSize: 15,
    color: '#666',
    lineHeight: 22,
    marginBottom: 20,
  },
  link: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 5,
    elevation: 2,
  },
  linkIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: COLORS.navbarBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  linkIconText: {
    fontSize: 18,
  },
  linkText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
    color: '#111',
  },
  linkArrow: {
    color: COLORS.navbarBg,
    fontSize: 18,
    fontWeight: '700',
  },
  image: {
    width: '100%',
    height: 250,
    borderRadius: 20,
    marginTop: 20,
  },
});