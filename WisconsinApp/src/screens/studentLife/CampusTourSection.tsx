import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

export default function CampusTourSection() {
  return (
    <View style={styles.container}>
      <Image
        source={require('../../assets/images/campus_tour.png')}
        style={styles.bgImage}
        resizeMode="cover"
      />
      <View style={styles.overlay} />

      <View style={styles.content}>
        <View style={styles.titleWrapper}>
          <View style={styles.redLine} />
          <View>
            <Text style={styles.title}>Madison, WI :</Text>
            <Text style={styles.subtitle}>
              The ultimate <Text style={styles.highlight}>college</Text> town
            </Text>
          </View>
        </View>

        <Text style={styles.description}>
          This is where big-city opportunities meet small-town conveniences.
          Where vibrant streetscapes lead to lakeside retreats.{' '}
          <Text style={styles.bold}>Welcome to Madison.</Text>
        </Text>

        <View style={styles.buttonsRow}>
          <TouchableOpacity style={styles.button}>
            <Text style={styles.buttonText}>Tour campus virtually</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.button}>
            <Text style={styles.buttonText}>
              Explore Madison in every season
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    minHeight: 400,
    justifyContent: 'center',
  },
  bgImage: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.45)',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  titleWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 14,
    marginBottom: 20,
  },
  redLine: {
    width: 5,
    height: 70,
    backgroundColor: COLORS.navbarBg,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.white,
  },
  subtitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.white,
  },
  highlight: {
    color: COLORS.navbarBg,
  },
  description: {
    fontSize: 15,
    lineHeight: 24,
    color: COLORS.white,
    marginBottom: 24,
  },
  bold: {
    fontWeight: '700',
    fontStyle: 'italic',
  },
  buttonsRow: {
    gap: 12,
  },
  button: {
    borderWidth: 2,
    borderColor: COLORS.white,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
});