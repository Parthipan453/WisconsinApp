import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS } from '../../../constants/colors';

interface SideCardProps {
  icon: string;
  title: string;
  isActive?: boolean;
  onPress?: () => void;
}

function SideCard({ icon, title, isActive, onPress }: SideCardProps) {
  return (
    <TouchableOpacity
      style={[styles.sideCard, isActive && styles.sideCardActive]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.sideLeft}>
        <View style={styles.iconCircle}>
          <Text style={styles.iconText}>{icon}</Text>
        </View>
        <Text style={styles.sideText}>{title}</Text>
      </View>
      <Text style={styles.chevron}>›</Text>
    </TouchableOpacity>
  );
}

export default function CoursesRightSidebar() {
  return (
    <View style={styles.container}>
      <Image
        source={require('../../../assets/images/university-logo-png.png')}
        style={styles.uwLogo}
        resizeMode="contain"
      />

      <SideCard icon="📅" title="Overview" isActive />
      <SideCard icon="📅" title="Course Designations" />
      <SideCard icon="📅" title="Course Requisites" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 12,
  },
  uwLogo: {
    width: 120,
    height: 80,
    alignSelf: 'center',
    marginBottom: 8,
  },
  sideCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E3E1DB',
    paddingVertical: 14,
    paddingHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sideCardActive: {
    borderLeftWidth: 4,
    borderLeftColor: COLORS.navbarBg,
    paddingLeft: 12,
  },
  sideLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#f6e2e3',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 16,
  },
  sideText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111',
    flex: 1,
  },
  chevron: {
    fontSize: 20,
    color: '#999',
    fontWeight: '300',
  },
});