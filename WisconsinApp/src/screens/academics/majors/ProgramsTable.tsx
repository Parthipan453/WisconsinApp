import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { COLORS } from '../../../constants/colors';
import { getPrograms, Program } from '../../../services/programs';
import { FilterState } from './MajorsIntroSection';

interface ProgramsTableProps {
  navigation: any;
  filters: FilterState;
}

export default function ProgramsTable({
  navigation,
  filters,
}: ProgramsTableProps) {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Debounce for search
    const timer = setTimeout(() => {
      loadPrograms();
    }, 300);

    return () => clearTimeout(timer);
  }, [filters.search, filters.programType, filters.interests]);

  const loadPrograms = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPrograms({
        search: filters.search,
        programType: filters.programType,
        interests: filters.interests,
      });
      setPrograms(data);
    } catch (err: any) {
      console.error('Error loading programs:', err);
      setError('Failed to load programs. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.navbarBg} />
        <Text style={styles.loadingText}>Loading programs...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadPrograms}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>
        All programs shown ({programs.length}).
      </Text>

      <View style={styles.tableWrapper}>
        <View style={styles.tableHeader}>
          <Text style={[styles.headerCell, styles.firstCell]}>
            Area of Study
          </Text>
          <Text style={[styles.headerCell, styles.lastCell]}>
            Program Type
          </Text>
        </View>

        <FlatList
          data={programs}
          keyExtractor={(item) => item.id.toString()}
          scrollEnabled={false}
          renderItem={({ item, index }) => (
            <View
              style={[
                styles.tableRow,
                index % 2 === 1 && styles.tableRowEven,
              ]}
            >
              <Text style={[styles.cell, styles.firstCell]}>{item.name}</Text>
              <Text style={[styles.cell, styles.lastCell, styles.typeCell]}>
                {item.degree}
              </Text>
            </View>
          )}
          ListEmptyComponent={
            <View style={styles.emptyRow}>
              <Text style={styles.emptyText}>
                No programs match your filters
              </Text>
            </View>
          }
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.white,
  },
  centerContainer: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.white,
    minHeight: 200,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
  },
  errorText: {
    fontSize: 14,
    color: '#c62828',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: COLORS.navbarBg,
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 6,
  },
  retryText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  heading: {
    fontSize: 15,
    fontWeight: '600',
    color: '#444',
    marginBottom: 12,
  },
  tableWrapper: {
    borderRadius: 8,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E3E1DB',
    backgroundColor: COLORS.white,
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: COLORS.navbarBg,
  },
  headerCell: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    padding: 14,
  },
  tableRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#EEEBE5',
    backgroundColor: COLORS.white,
  },
  tableRowEven: {
    backgroundColor: '#F2F1ED',
  },
  cell: {
    fontSize: 14,
    color: '#111',
    padding: 14,
  },
  typeCell: {
    color: '#004B87',
    fontWeight: '700',
  },
  firstCell: {
    flex: 2,
  },
  lastCell: {
    flex: 1,
  },
  emptyRow: {
    padding: 30,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
  },
});