import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS } from '../../constants/colors';

export default function CourseFooter() {
  return (
    <View style={styles.container}>
      {/* Main footer */}
      <View style={styles.mainFooter}>
        <Text style={styles.footerTitle}>University of Wisconsin-Madison</Text>
        <Text style={styles.footerSub}>
          © 2026-2027 Board of Regents of the University of Wisconsin System
        </Text>

        <View style={styles.linksRow}>
          <TouchableOpacity>
            <Text style={styles.link}>Privacy Statement</Text>
          </TouchableOpacity>
          <Text style={styles.separator}>|</Text>
          <TouchableOpacity>
            <Text style={styles.link}>Accessibility</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Copyright bar */}
      <View style={styles.copyrightBar}>
        <Text style={styles.copyrightText}>
          Feedback: guideditor@office365.wisc.edu
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#f5f5f5',
    paddingTop: 24,
  },
  mainFooter: {
    paddingHorizontal: 16,
    paddingBottom: 24,
    alignItems: 'center',
  },
  footerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#222',
    marginBottom: 8,
    textAlign: 'center',
  },
  footerSub: {
    fontSize: 12,
    color: '#555',
    textAlign: 'center',
    marginBottom: 16,
  },
  linksRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  link: {
    fontSize: 13,
    color: COLORS.navbarBg,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  separator: {
    color: '#999',
    paddingHorizontal: 8,
  },
  copyrightBar: {
    backgroundColor: '#930000',
    paddingVertical: 16,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  copyrightText: {
    fontSize: 12,
    color: COLORS.white,
    textAlign: 'center',
  },
});