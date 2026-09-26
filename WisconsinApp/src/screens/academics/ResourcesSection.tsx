import React from 'react';
import { View, Text, TouchableOpacity, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const RESOURCES = [
  { id: 1, label: 'Academic advising', screen: 'Advising' },
  { id: 2, label: 'Academic calendar', screen: 'Calendar' },
  { id: 3, label: 'Departments and programs', screen: 'Departments' },
  { id: 4, label: 'Registrar', screen: 'Registrar' },
  { id: 5, label: 'Schools and colleges', screen: 'Schools' },
  { id: 6, label: 'Undergraduate research', screen: 'Research' },
];

export default function ResourcesSection({ navigation }: any) {
  return (
    <ImageBackground
      source={require('../../assets/images/sealimage.jpg')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <View style={styles.line} />
        <Text style={styles.heading}>Resources</Text>

        {RESOURCES.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={styles.resourceCard}
            onPress={() => navigation && navigation.navigate(item.screen)}
          >
            <Text style={styles.resourceText}>{item.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: 400,
    paddingVertical: 40,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  line: {
    width: 70,
    height: 6,
    backgroundColor: COLORS.white,
    alignSelf: 'center',
    borderRadius: 20,
    marginBottom: 16,
  },
  heading: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 30,
  },
  resourceCard: {
    backgroundColor: COLORS.white,
    borderRadius: 14,
    paddingVertical: 20,
    paddingHorizontal: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 5,
    alignItems: 'center',
  },
  resourceText: {
    color: COLORS.navbarBg,
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});