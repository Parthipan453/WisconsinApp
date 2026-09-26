import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const RANKINGS = [
  { id: 1, target: 12, label: 'Best public university\n(2026)' },
  { id: 2, target: 1, label: 'Best public university\n(2026)' },
  { id: 3, target: 22, label: 'Best public university\n(2026)' },
  { id: 4, target: 43, label: 'Best public university\n(2026)' },
];

function Counter({ target }: { target: number }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const duration = 2000;
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    const interval = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(interval);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(interval);
  }, [target]);

  return <Text style={styles.number}>#{count}</Text>;
}

export default function RankingSection() {
  return (
    <ImageBackground
      source={require('../../assets/images/bg_about.jpg')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <View style={styles.grid}>
          {RANKINGS.map((item) => (
            <View key={item.id} style={styles.card}>
              <Counter target={item.target} />
              <View style={styles.whiteLine} />
              <Text style={styles.label}>{item.label}</Text>
            </View>
          ))}
        </View>

        <TouchableOpacity style={styles.factsButton}>
          <Text style={styles.factsButtonText}>Explore more UW facts →</Text>
        </TouchableOpacity>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: 500,
    paddingVertical: 40,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(96,16,16,0.3)',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  card: {
    width: '48%',
    alignItems: 'center',
    marginBottom: 24,
  },
  number: {
    fontSize: 44,
    fontWeight: '700',
    color: COLORS.white,
  },
  whiteLine: {
    width: 50,
    height: 3,
    backgroundColor: COLORS.white,
    marginVertical: 12,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.white,
    textAlign: 'center',
    lineHeight: 20,
  },
  factsButton: {
    backgroundColor: COLORS.white,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignSelf: 'center',
    marginTop: 12,
  },
  factsButtonText: {
    color: COLORS.navbarBg,
    fontSize: 15,
    fontWeight: '600',
  },
});