import React, { useState } from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import FilterSidebar from './FilterSidebar';
import ProgramsTable from './ProgramsTable';
import { COLORS, SIZES } from '../../../constants/colors';

export interface FilterState {
  search: string;
  programType: string;
  interests: number[];
}

export default function MajorsIntroSection({ navigation }: any) {
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    programType: 'all',
    interests: [],
  });

  return (
    <View style={styles.container}>
      <View style={styles.topLine} />
      <Text style={styles.title}>
        Undergraduate majors and certificates
      </Text>

      <View style={styles.divider}>
        <View style={styles.dividerLine} />
        <Image
          source={require('../../../assets/images/logo-Photoroom.png')}
          style={styles.dividerLogo}
        />
        <View style={styles.dividerLine} />
      </View>

      <Text style={styles.paragraph}>
        The University of Wisconsin–Madison offers hundreds of undergraduate
        majors and certificates. A major is a specialized area of study that
        includes a set of defined core classes and electives ranging from
        introductory to advanced coursework.
      </Text>

      <View style={styles.bottomLine} />

      {/* Filters + Table */}
      <View style={styles.mainGrid}>
        <FilterSidebar filters={filters} onFiltersChange={setFilters} />
        <ProgramsTable navigation={navigation} filters={filters} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F5',
    paddingHorizontal: SIZES.padding,
    paddingVertical: 30,
  },
  topLine: {
    width: 70,
    height: 5,
    backgroundColor: COLORS.navbarBg,
    alignSelf: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111',
    textAlign: 'center',
    marginBottom: 20,
    fontFamily: 'serif',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    gap: 10,
  },
  dividerLine: {
    width: 100,
    height: 1,
    backgroundColor: '#BDBDBD',
  },
  dividerLogo: {
    width: 40,
    height: 40,
    resizeMode: 'contain',
  },
  paragraph: {
    fontSize: 15,
    lineHeight: 24,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  bottomLine: {
    width: '100%',
    height: 3,
    backgroundColor: COLORS.navbarBg,
    marginBottom: 30,
  },
  mainGrid: {
    flexDirection: 'column',
    gap: 20,
  },
});