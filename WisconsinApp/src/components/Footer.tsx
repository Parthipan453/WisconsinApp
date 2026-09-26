import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { COLORS } from '../constants/colors';
import {
  FOOTER_POPULAR,
  FOOTER_RESOURCES,
  FOOTER_QUICK_LINKS,
} from '../constants/navItems';

export default function Footer() {
  const year = new Date().getFullYear();

  const renderColumn = (title: string, items: string[]) => (
    <View style={styles.footerColumn}>
      <Text style={styles.columnTitle}>{title}</Text>
      {items.map((item) => (
        <TouchableOpacity key={item}>
          <Text style={styles.columnLink}>{item}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  return (
    <View style={styles.footer}>
      <View style={styles.searchBand}>
        <Text style={styles.searchTitle}>
          Are you searching for something specific?
        </Text>
      </View>

      <View style={styles.footerMain}>
        <View style={styles.logoBox}>
          <Text style={styles.logoText}>UW</Text>
          <Text style={styles.logoCaption}>
            Part of the Universities of Wisconsin
          </Text>
          <View style={styles.socialRow}>
            {['f', 'X', 'in', 'ig', 'yt'].map((icon) => (
              <View key={icon} style={styles.socialIcon}>
                <Text style={styles.socialText}>{icon}</Text>
              </View>
            ))}
          </View>
        </View>

        {renderColumn('Popular', FOOTER_POPULAR)}
        {renderColumn('Resources', FOOTER_RESOURCES)}
        {renderColumn('Quick Links', FOOTER_QUICK_LINKS)}
      </View>

      <View style={styles.footerBottom}>
        <Text style={styles.copyright}>
          © {year} Board of Regents of the University of Wisconsin System
        </Text>
        <Text style={styles.copyrightLink}>Privacy notice</Text>
        <Text style={styles.copyrightSmall}>
          web.strategiccommunication@wisc.edu
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  footer: {
    backgroundColor: COLORS.footer,
  },
  searchBand: {
    backgroundColor: COLORS.navbarBg,
    padding: 20,
    alignItems: 'center',
  },
  searchTitle: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '500',
    textAlign: 'center',
  },
  footerMain: {
    padding: 24,
  },
  logoBox: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logoText: {
    color: COLORS.white,
    fontSize: 32,
    fontWeight: '900',
    letterSpacing: 2,
    marginBottom: 8,
  },
  logoCaption: {
    color: 'rgba(255,255,255,0.85)',
    fontSize: 14,
    marginBottom: 16,
  },
  socialRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  socialIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: COLORS.white,
    justifyContent: 'center',
    alignItems: 'center',
    margin: 5,
  },
  socialText: {
    color: COLORS.navbarBg,
    fontSize: 14,
    fontWeight: 'bold',
  },
  footerColumn: {
    marginBottom: 24,
  },
    columnTitle: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: 2,
    borderBottomColor: 'rgba(255,255,255,0.4)',
    alignSelf: 'flex-start',  // ← இது add பண்ணுங்க
    },
  columnLink: {
    color: 'rgba(255,255,255,0.88)',
    fontSize: 15,
    paddingVertical: 6,
  },
  footerBottom: {
    backgroundColor: COLORS.navbarBg,
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.3)',
    alignItems: 'center',
  },
  copyright: {
    color: 'rgba(255,255,255,0.75)',
    fontSize: 12,
    textAlign: 'center',
    marginBottom: 6,
  },
  copyrightLink: {
    color: 'rgba(255,255,255,0.75)',
    fontSize: 12,
    textDecorationLine: 'underline',
    marginBottom: 6,
  },
  copyrightSmall: {
    color: 'rgba(255,255,255,0.6)',
    fontSize: 11,
    textAlign: 'center',
  },
});