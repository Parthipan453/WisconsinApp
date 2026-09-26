import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

export default function CoursesBreadcrumb() {
  return (
    <View style={styles.container}>
      <Text style={styles.homeIcon}>🏠</Text>
      <TouchableOpacity>
        <Text style={styles.link}>Home</Text>
      </TouchableOpacity>
      <Text style={styles.separator}>›</Text>
      <Text style={styles.current}>Courses</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 6,
  },
  homeIcon: {
    fontSize: 14,
  },
  link: {
    color: '#c5050c',
    fontSize: 14,
    fontWeight: '500',
    textDecorationLine: 'underline',
  },
  separator: {
    color: '#999',
    fontSize: 18,
    marginHorizontal: 2,
  },
  current: {
    color: '#333',
    fontSize: 14,
    fontWeight: '600',
  },
});