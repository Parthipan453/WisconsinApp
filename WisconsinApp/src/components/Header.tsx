import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { COLORS, SIZES } from '../constants/colors';
import { TOP_NAV_ITEMS, MAIN_NAV_ITEMS } from '../constants/navItems';

interface HeaderProps {
  navigation: any;
  activeScreen?: string;
}

export default function Header({ navigation, activeScreen }: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  const handleNavigate = (screen: string) => {
    setMenuOpen(false);
    navigation.navigate(screen);
  };

  return (
    <>
      <View style={styles.headerBand}>
        <View style={styles.navbarCard}>
          <TouchableOpacity
            style={styles.logoContainer}
            onPress={() => handleNavigate('Home')}
          >
            <Text style={styles.logoText}>UW</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.toggle}
            onPress={() => {
                console.log('☰ Tapped! Current menuOpen:', menuOpen);
                setMenuOpen(!menuOpen);
                console.log('☰ New menuOpen:', !menuOpen);
            }}
            >
            <Text style={styles.toggleIcon}>{menuOpen ? '✕' : '☰'}</Text>
           </TouchableOpacity>
        </View>
      </View>

      <Modal
        visible={menuOpen}
        animationType="slide"
        onRequestClose={() => setMenuOpen(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Menu</Text>
            <TouchableOpacity onPress={() => setMenuOpen(false)}>
              <Text style={styles.closeIcon}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <Text style={styles.sectionLabel}>QUICK LINKS</Text>
            {TOP_NAV_ITEMS.map((item) => (
              <TouchableOpacity
                key={item.screen}
                style={styles.menuItem}
                onPress={() => handleNavigate(item.screen)}
              >
                <Text
                  style={[
                    styles.menuItemText,
                    activeScreen === item.screen && styles.menuItemActive,
                  ]}
                >
                  {item.label}
                </Text>
              </TouchableOpacity>
            ))}

            <Text style={[styles.sectionLabel, { marginTop: 24 }]}>
              EXPLORE
            </Text>
            {MAIN_NAV_ITEMS.map((item) => (
              <TouchableOpacity
                key={item.screen}
                style={styles.menuItem}
                onPress={() => handleNavigate(item.screen)}
              >
                <Text
                  style={[
                    styles.menuItemText,
                    activeScreen === item.screen && styles.menuItemActive,
                  ]}
                >
                  {item.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  headerBand: {
    backgroundColor: COLORS.navbarBg,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  navbarCard: {
    backgroundColor: COLORS.white,
    borderRadius: SIZES.borderRadius,
    paddingHorizontal: 20,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoText: {
    color: COLORS.navbarBg,
    fontSize: 24,
    fontWeight: '900',
    letterSpacing: 2,
  },
  toggle: {
    padding: 6,
  },
  toggleIcon: {
    color: COLORS.navbarBg,
    fontSize: 24,
    fontWeight: 'bold',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  modalHeader: {
    backgroundColor: COLORS.navbarBg,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
  },
  modalTitle: {
    color: COLORS.white,
    fontSize: 20,
    fontWeight: 'bold',
  },
  closeIcon: {
    color: COLORS.white,
    fontSize: 24,
  },
  modalContent: {
    padding: SIZES.padding,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.textLight,
    letterSpacing: 2,
    marginBottom: 12,
  },
  menuItem: {
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  menuItemText: {
    fontSize: 16,
    color: COLORS.text,
    fontWeight: '500',
  },
  menuItemActive: {
    color: COLORS.navbarBg,
    fontWeight: '700',
  },
});