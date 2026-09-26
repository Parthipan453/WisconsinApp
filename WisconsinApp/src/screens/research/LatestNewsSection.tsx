import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const NEWS = [
  {
    id: 1,
    image: require('../../assets/images/latest_new_1.jpg'),
    number: '01',
    title: 'The two Owens',
    description: 'The death of a six-year-old inspired a UW-Madison researcher to investigate a rare brain cancer.',
  },
  {
    id: 2,
    image: require('../../assets/images/latest_new_2.jpg'),
    number: '02',
    title: 'Zika infections can cause significant developmental problems',
    description: 'Even babies born without the virus notable physical symptoms may experience sensory and anxiety issues.',
  },
  {
    id: 3,
    image: require('../../assets/images/latest_new_3.jpg'),
    number: '03',
    title: 'Detailed molecular picture of tooth enamel reveals adaptions to diets',
    description: 'Research led by UW-Madison physics professor suggests enamel evolved to become tougher over millions of years.',
  },
];

export default function LatestNewsSection() {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.topLine} />
        <Text style={styles.title}>Latest news</Text>
        <Text style={styles.subtitle}>
          Discover the latest research, stories, and breakthroughs from UW-Madison
        </Text>
      </View>

      {NEWS.map((news) => (
        <View key={news.id} style={styles.newsItem}>
          <Image source={news.image} style={styles.newsImage} />
          <View style={styles.newsBody}>
            <Text style={styles.newsNumber}>{news.number}</Text>
            <Text style={styles.newsTitle}>{news.title}</Text>
            <Text style={styles.newsDescription}>{news.description}</Text>
            <TouchableOpacity>
              <Text style={styles.newsArrow}>→</Text>
            </TouchableOpacity>
          </View>
        </View>
      ))}

      <TouchableOpacity style={styles.button}>
        <Text style={styles.buttonText}>Read more research news →</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    padding: SIZES.padding * 1.5,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  topLine: {
    width: 60,
    height: 5,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 13,
    color: '#333',
    textAlign: 'center',
  },
  newsItem: {
    backgroundColor: COLORS.white,
    borderRadius: 10,
    overflow: 'hidden',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  newsImage: {
    width: '100%',
    height: 180,
    resizeMode: 'cover',
  },
  newsBody: {
    padding: 16,
  },
  newsNumber: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111',
    marginBottom: 8,
  },
  newsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
    marginBottom: 8,
  },
  newsDescription: {
    fontSize: 14,
    color: '#222',
    lineHeight: 20,
    marginBottom: 12,
  },
  newsArrow: {
    color: COLORS.navbarBg,
    fontSize: 22,
    fontWeight: '700',
    alignSelf: 'flex-end',
  },
  button: {
    backgroundColor: COLORS.navbarBg,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 25,
    alignSelf: 'center',
    marginTop: 12,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
});