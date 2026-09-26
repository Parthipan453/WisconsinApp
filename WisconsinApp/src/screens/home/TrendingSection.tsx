import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const CARDS = [
  { id: 1, image: require('../../assets/images/news2.jpg'), tag: 'SPRING COMMENCEMENT', text: 'Tears of joy, words of advice mark Saturday commencement' },
  { id: 2, image: require('../../assets/images/news3.jpg'), tag: 'SPRING COMMENCEMENT', text: 'UW celebrates doctoral and professional graduates' },
  { id: 3, image: require('../../assets/images/news4.jpg'), tag: 'MENTORING AWARDS', text: 'Going above and beyond to help students succeed' },
  { id: 4, image: require('../../assets/images/news2.jpg'), tag: 'CAMPUS BUILDINGS', text: '$85.2 million gift will support Science Hall transformation' },
];

export default function TrendingSection() {
  return (
    <View style={styles.container}>
      {/* Header */}
      <Text style={styles.eyebrow}>| TRENDING ON CAMPUS</Text>
      <Text style={styles.title}>Stories shaping life at UW</Text>
      <Text style={styles.subtitle}>
        From campus highlights to student success, explore what is happening at Wisconsin.
      </Text>

      {/* Featured Story */}
      <View style={styles.featured}>
        <Image source={require('../../assets/images/news1.jpg')} style={styles.featuredImg} />
        <View style={styles.featuredContent}>
          <Text style={styles.featuredTitle}>State Street, that Great Street</Text>
          <Text style={styles.featuredDesc}>
            Take a stroll down the iconic campus corridor, where old favorites meet new trends.
          </Text>
          <TouchableOpacity style={styles.readBtn}>
            <Text style={styles.readBtnText}>Read full story →</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Cards */}
      {CARDS.map((card) => (
        <View key={card.id} style={styles.card}>
          <Image source={card.image} style={styles.cardImg} />
          <View style={styles.cardBody}>
            <Text style={styles.cardTag}>{card.tag}</Text>
            <Text style={styles.cardText}>{card.text}</Text>
            <Text style={styles.cardArrow}>→</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: SIZES.padding,
    marginBottom: 40,
  },
  eyebrow: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.navbarBg,
    letterSpacing: 1,
    marginBottom: 6,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
    marginBottom: 20,
  },
  featured: {
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
  },
  featuredImg: {
    width: '100%',
    height: 200,
  },
  featuredContent: {
    backgroundColor: COLORS.navbarBg,
    padding: 20,
  },
  featuredTitle: {
    fontSize: 22,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 8,
  },
  featuredDesc: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.92)',
    lineHeight: 20,
    marginBottom: 12,
  },
  readBtn: {
    backgroundColor: COLORS.white,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  readBtnText: {
    color: COLORS.navbarBg,
    fontSize: 13,
    fontWeight: '700',
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 10,
    overflow: 'hidden',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  cardImg: {
    width: '100%',
    height: 160,
  },
  cardBody: {
    padding: 14,
    backgroundColor: '#F3F0EC',
  },
  cardTag: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.navbarBg,
    letterSpacing: 1,
    marginBottom: 6,
  },
  cardText: {
    fontSize: 14,
    color: '#1A1A1A',
    lineHeight: 20,
    marginBottom: 8,
  },
  cardArrow: {
    fontSize: 18,
    color: COLORS.navbarBg,
    fontWeight: '700',
  },
});