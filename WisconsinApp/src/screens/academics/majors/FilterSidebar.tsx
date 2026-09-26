import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { COLORS } from '../../../constants/colors';
import { getInterests, Interest } from '../../../services/interests';
import { FilterState } from './MajorsIntroSection';

const PROGRAM_TYPES = [
  { id: 'all', label: 'All majors and certificates' },
  { id: 'FULL_TIME', label: 'Full Time' },
  { id: 'PART_TIME', label: 'Part Time' },
  { id: 'ONLINE', label: 'Online' },
];

interface FilterSidebarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
}

export default function FilterSidebar({
  filters,
  onFiltersChange,
}: FilterSidebarProps) {
  const [interests, setInterests] = useState<Interest[]>([]);
  const [loadingInterests, setLoadingInterests] = useState(true);

  useEffect(() => {
    loadInterests();
  }, []);

  const loadInterests = async () => {
    try {
      const data = await getInterests();
      setInterests(data);
    } catch (error) {
      console.error('Error loading interests:', error);
    } finally {
      setLoadingInterests(false);
    }
  };

  const handleSearchChange = (text: string) => {
    onFiltersChange({ ...filters, search: text });
  };

  const handleTypeChange = (type: string) => {
    onFiltersChange({ ...filters, programType: type });
  };

  const toggleInterest = (id: number) => {
    const current = filters.interests;
    const updated = current.includes(id)
      ? current.filter((i) => i !== id)
      : [...current, id];
    onFiltersChange({ ...filters, interests: updated });
  };

  const clearFilters = () => {
    onFiltersChange({
      search: '',
      programType: 'all',
      interests: [],
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Search programs</Text>

      <TextInput
        style={styles.input}
        placeholder="Search by keyword"
        placeholderTextColor="#999"
        value={filters.search}
        onChangeText={handleSearchChange}
      />

      <View style={styles.filterHeader}>
        <Text style={styles.filterTitle}>Filter by</Text>
        <TouchableOpacity onPress={clearFilters}>
          <Text style={styles.clearButton}>Clear filters</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.subheading}>Program Type</Text>

      {PROGRAM_TYPES.map((type) => (
        <TouchableOpacity
          key={type.id}
          style={styles.radioRow}
          onPress={() => handleTypeChange(type.id)}
          activeOpacity={0.7}
        >
          <View
            style={[
              styles.radioOuter,
              filters.programType === type.id && styles.radioOuterActive,
            ]}
          >
            {filters.programType === type.id && (
              <View style={styles.radioInner} />
            )}
          </View>
          <Text style={styles.radioLabel}>{type.label}</Text>
        </TouchableOpacity>
      ))}

      <Text style={styles.subheading}>Areas of interest</Text>

      {loadingInterests ? (
        <ActivityIndicator size="small" color={COLORS.navbarBg} />
      ) : interests.length === 0 ? (
        <Text style={styles.noInterests}>No interests available</Text>
      ) : (
        interests.map((interest) => (
          <TouchableOpacity
            key={interest.id}
            style={styles.checkboxRow}
            onPress={() => toggleInterest(interest.id)}
            activeOpacity={0.7}
          >
            <View
              style={[
                styles.checkbox,
                filters.interests.includes(interest.id) &&
                  styles.checkboxActive,
              ]}
            >
              {filters.interests.includes(interest.id) && (
                <Text style={styles.checkmark}>✓</Text>
              )}
            </View>
            <Text style={styles.checkboxLabel}>{interest.name}</Text>
          </TouchableOpacity>
        ))
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E3E1DB',
    padding: 20,
  },
  heading: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111',
    marginBottom: 16,
    fontFamily: 'serif',
  },
  input: {
    borderWidth: 1,
    borderColor: '#CCC',
    borderRadius: 4,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#111',
    marginBottom: 20,
  },
  filterHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#EEE',
    paddingTop: 16,
    marginBottom: 14,
  },
  filterTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111',
  },
  clearButton: {
    color: '#CC0000',
    fontSize: 13,
    textDecorationLine: 'underline',
  },
  subheading: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111',
    marginBottom: 12,
    marginTop: 12,
    fontFamily: 'serif',
  },
  noInterests: {
    fontSize: 13,
    color: '#999',
    fontStyle: 'italic',
  },
  radioRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 10,
  },
  radioOuter: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: '#CCC',
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioOuterActive: {
    borderColor: COLORS.navbarBg,
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: COLORS.navbarBg,
  },
  radioLabel: {
    fontSize: 14,
    color: '#444',
    flex: 1,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 10,
  },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 3,
    borderWidth: 2,
    borderColor: '#CCC',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxActive: {
    backgroundColor: COLORS.navbarBg,
    borderColor: COLORS.navbarBg,
  },
  checkmark: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: 'bold',
  },
  checkboxLabel: {
    fontSize: 14,
    color: '#444',
    flex: 1,
  },
});