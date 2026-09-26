import React from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  StyleSheet,
} from 'react-native';
import { COLORS } from '../../constants/colors';

export default function CourseHeader() {
  return (
    <View style={styles.container}>
      {/* Logo Row */}
      <View style={styles.logoRow}>
        <Image
          source={require('../../assets/images/wisconsin-logo-png.png')}
          style={styles.logo}
          resizeMode="contain"
        />
        <View>
          <Text style={styles.guideText}>Guide</Text>
          <Text style={styles.yearText}>2026 - 2027</Text>
        </View>
      </View>

      {/* Search Bar */}
      <View style={styles.searchRow}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search the Guide"
          placeholderTextColor="#999"
        />
        <TouchableOpacity style={styles.searchButton}>
          <Text style={styles.searchIcon}>🔍</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#ececec',
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
    marginBottom: 16,
  },
  logo: {
    width: 100,
    height: 100,
  },
  guideText: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.navbarBg,
    fontFamily: 'serif',
    lineHeight: 34,
  },
  yearText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#222',
    marginTop: 2,
  },
  searchRow: {
    flexDirection: 'row',
    height: 44,
  },
  searchInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#cfcfcf',
    borderRightWidth: 0,
    paddingHorizontal: 12,
    fontSize: 14,
    color: '#111',
    backgroundColor: COLORS.white,
  },
  searchButton: {
    width: 60,
    backgroundColor: COLORS.navbarBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchIcon: {
    fontSize: 18,
  },
});