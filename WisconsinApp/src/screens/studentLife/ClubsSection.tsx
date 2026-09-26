import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function ClubsSection() {
  return (
    <View style={styles.container}>
      <Image
        source={require('../../assets/images/Club-left-image.png')}
        style={styles.image}
        resizeMode="cover"
      />
      <View style={styles.content}>
        <View style={styles.redLine} />
        <Text style={styles.title}>
          Clubs and <Text style={styles.highlight}>student organizations</Text>
        </Text>
        <Text style={styles.description}>
          You're just a few clicks away from finding community among campus's
          nearly 1,000 clubs and organizations.
        </Text>
        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>
            Learn more about the Wisconsin
          </Text>
          <View style={styles.arrowCircle}>
            <Text style={styles.arrow}>→</Text>
          </View>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 40,
    backgroundColor: COLORS.white,
  },
  image: {
    width: '100%',
    height: 240,
    borderTopRightRadius: 40,
    borderBottomLeftRadius: 40,
  },
  content: {
    paddingHorizontal: SIZES.padding,
    paddingTop: 24,
  },
  redLine: {
    width: 60,
    height: 4,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: COLORS.text,
    lineHeight: 30,
    marginBottom: 14,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  description: {
    fontSize: 14,
    lineHeight: 22,
    color: '#555',
    marginBottom: 20,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.white,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 3,
  },
  buttonText: {
    color: COLORS.navbarBg,
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  arrowCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.black,
    justifyContent: 'center',
    alignItems: 'center',
  },
  arrow: {
    color: COLORS.white,
    fontSize: 16,
  },
});