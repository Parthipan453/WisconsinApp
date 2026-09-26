import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function CourseTopBar() {
  return (
    <View style={styles.container}>
      <Text style={styles.link}>UNIVERSITY of WISCONSIN-MADISON</Text>
      <Text style={styles.separator}>|</Text>
      <Text style={styles.link}>FACULTY</Text>
      <Text style={styles.separator}>|</Text>
      <Text style={styles.link}>ARCHIVE</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#f7f7f7',
    borderBottomWidth: 1,
    borderBottomColor: '#d8d8d8',
    paddingVertical: 14,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
  },
  link: {
    fontSize: 11,
    fontWeight: '700',
    color: '#1f1f1f',
    letterSpacing: 0.3,
  },
  separator: {
    color: '#cfcfcf',
    fontSize: 12,
    marginHorizontal: 4,
  },
});