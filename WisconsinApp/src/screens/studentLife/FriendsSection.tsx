import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const FRIENDS_DATA = [
  {
    id: 1,
    image: require('../../assets/images/left-slid-show.jpg'),
    title: 'Campus housing',
    description:
      'Our residence halls offer a range of personality in two distinct neighborhoods: Lakeshore for the nature lover and Southeast for the city soul.',
  },
  {
    id: 2,
    image: require('../../assets/images/right-image-friends.jpg'),
    title: 'Campus housing',
    description:
      'Our residence halls offer a range of personality in two distinct neighborhoods: Lakeshore for the nature lover and Southeast for the city soul.',
  },
  {
    id: 3,
    image: require('../../assets/images/Left-image-friends.jpg'),
    title: 'Campus housing',
    description:
      'Our residence halls offer a range of personality in two distinct neighborhoods: Lakeshore for the nature lover and Southeast for the city soul.',
  },
];

export default function FriendsSection() {
  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.verticalLine} />
          <Text style={styles.headerTitle}>
            Where you'll make friends and memories to{' '}
            <Text style={styles.highlight}>last a lifetime</Text>
          </Text>
        </View>
      </View>

      {/* Rows */}
      {FRIENDS_DATA.map((item, index) => (
        <View key={item.id} style={styles.row}>
          <Image source={item.image} style={styles.image} resizeMode="cover" />
          <View style={styles.content}>
            <View style={styles.titleWrap}>
              <Text style={styles.icon}>🏠</Text>
              <View style={styles.smallLine} />
              <Text style={styles.rowTitle}>{item.title}</Text>
            </View>
            <Text style={styles.description}>{item.description}</Text>
            <TouchableOpacity>
              <Text style={styles.link}>Explore housing options →</Text>
            </TouchableOpacity>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F8F8F8',
    paddingVertical: 40,
    paddingHorizontal: SIZES.padding,
  },
  header: {
    marginBottom: 24,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  verticalLine: {
    width: 5,
    height: 60,
    backgroundColor: COLORS.navbarBg,
  },
  headerTitle: {
    flex: 1,
    fontSize: 22,
    fontWeight: '600',
    color: COLORS.text,
    lineHeight: 28,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  row: {
    marginBottom: 32,
  },
  image: {
    width: '100%',
    height: 180,
    borderRadius: 20,
    marginBottom: 16,
  },
  content: {
    paddingHorizontal: 4,
  },
  titleWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  icon: {
    fontSize: 22,
  },
  smallLine: {
    width: 3,
    height: 22,
    backgroundColor: COLORS.navbarBg,
  },
  rowTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.text,
  },
  description: {
    fontSize: 14,
    lineHeight: 22,
    color: '#555',
    marginBottom: 12,
  },
  link: {
    color: COLORS.navbarBg,
    fontSize: 14,
    fontWeight: '600',
  },
});