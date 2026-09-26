import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { COLORS } from '../../../constants/colors';

const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

export default function CoursesSkipLetters() {
  const [activeLetter, setActiveLetter] = useState('A');

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Skip to letter:</Text>

      <View style={styles.lettersGrid}>
        {LETTERS.map((letter) => (
          <TouchableOpacity
            key={letter}
            style={[
              styles.letter,
              activeLetter === letter && styles.letterActive,
            ]}
            onPress={() => setActiveLetter(letter)}
            activeOpacity={0.7}
          >
            <Text
              style={[
                styles.letterText,
                activeLetter === letter && styles.letterTextActive,
              ]}
            >
              {letter}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#444',
    marginBottom: 10,
  },
  lettersGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  letter: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#CCC',
    backgroundColor: COLORS.white,
    justifyContent: 'center',
    alignItems: 'center',
  },
  letterActive: {
    backgroundColor: COLORS.navbarBg,
    borderColor: COLORS.navbarBg,
  },
  letterText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#333',
  },
  letterTextActive: {
    color: COLORS.white,
  },
});