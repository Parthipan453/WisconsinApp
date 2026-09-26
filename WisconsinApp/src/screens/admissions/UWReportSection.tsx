import React from 'react';
import { View, Text, TouchableOpacity, ImageBackground, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/colors';

const REPORTS = [
  {
    id: 1,
    title: 'Annual Security and Fire Safety Report',
    description: 'The Annual Security and Fire Safety Report contains current campus safety and disciplinary policies, crime statistics, and fire statistics for the previous three calendar years.',
    link: 'Download the most recent report (PDF)',
  },
  {
    id: 2,
    title: 'Voluntary System of Accountability',
    description: 'UW-Madison participates in the Voluntary System of Accountability, a program designed to provide accountability through accessible, transparent, and comparable information for more than 260 public colleges and universities.',
  },
];

export default function UWReportSection() {
  return (
    <ImageBackground
      source={require('../../assets/images/report_bg.png')}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.content}>
        {REPORTS.map((report) => (
          <View key={report.id} style={styles.card}>
            <View style={styles.headingRow}>
              <View style={styles.redBar} />
              <Text style={styles.cardTitle}>{report.title}</Text>
            </View>
            <Text style={styles.cardDescription}>{report.description}</Text>
            {report.link && (
              <TouchableOpacity style={styles.linkRow}>
                <Text style={styles.linkText}>{report.link}</Text>
                <Text style={styles.linkArrow}>→</Text>
              </TouchableOpacity>
            )}
          </View>
        ))}
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: 400,
    paddingVertical: 30,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(244,244,244,0.7)',
  },
  content: {
    padding: SIZES.padding,
  },
  card: {
    backgroundColor: 'rgba(255,255,255,0.85)',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  headingRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 14,
  },
  redBar: {
    width: 5,
    height: 40,
    backgroundColor: COLORS.navbarBg,
  },
  cardTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A1A',
    lineHeight: 22,
  },
  cardDescription: {
    fontSize: 14,
    color: '#333',
    lineHeight: 22,
    marginBottom: 14,
  },
  linkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  linkText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  linkArrow: {
    color: COLORS.navbarBg,
    fontSize: 22,
    fontWeight: '700',
  },
});