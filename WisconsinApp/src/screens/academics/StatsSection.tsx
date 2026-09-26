import React, { useEffect, useState } from 'react';
import { View, Text, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const STATS = [
  { id: 1, icon: '👥', target: 51822, label: 'Student Population', sub: '(Fall 2025)' },
  { id: 2, icon: '🎓', target: 2300, label: 'Faculty Members', sub: '(Current)' },
  { id: 3, icon: '📖', target: 9000, label: 'Courses Offered', sub: 'Every Year' },
  { id: 4, icon: '🏆', target: 400, label: 'Academic Programs', sub: 'Across Campus' },
];

function Counter({ target }: { target: number }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const duration = 1500;
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    const interval = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(interval);
      } else {
        setCount(Math.ceil(current));
      }
    }, duration / steps);

    return () => clearInterval(interval);
  }, [target]);

  return <Text style={styles.statNumber}>{count.toLocaleString()}</Text>;
}

export default function StatsSection() {
  return (
    <ImageBackground
      source={require('../../assets/images/foursectionimage.png')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        <View style={styles.headingLine} />
        <Text style={styles.heading}>
          Our world-class faculty focus on student success
        </Text>

        <View style={styles.statsGrid}>
          {STATS.map((stat) => (
            <View key={stat.id} style={styles.statBox}>
              <View style={styles.statIconCircle}>
                <Text style={styles.statIconText}>{stat.icon}</Text>
              </View>
              <Counter target={stat.target} />
              <Text style={styles.statLabel}>{stat.label}</Text>
              <Text style={styles.statSub}>{stat.sub}</Text>
            </View>
          ))}
        </View>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: 450,
    justifyContent: 'center',
    marginVertical: 40,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255,255,255,0.5)',
  },
  content: {
    padding: SIZES.padding * 1.5,
  },
  headingLine: {
    width: 100,
    height: 6,
    backgroundColor: COLORS.navbarBg,
    alignSelf: 'center',
    marginBottom: 16,
    borderRadius: 20,
  },
  heading: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1A1A1A',
    textAlign: 'center',
    marginBottom: 30,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statBox: {
    width: '48%',
    alignItems: 'center',
    marginBottom: 24,
  },
  statIconCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#F7DEDE',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  statIconText: {
    fontSize: 20,
  },
  statNumber: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  statLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.navbarBg,
    marginTop: 4,
    textAlign: 'center',
  },
  statSub: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
});