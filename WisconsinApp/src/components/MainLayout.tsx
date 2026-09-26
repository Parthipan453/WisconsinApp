import React from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Header from './Header';
import Footer from './Footer';
import { COLORS } from '../constants/colors';

interface MainLayoutProps {
  children: React.ReactNode;
  navigation: any;
  activeScreen?: string;
}

export default function MainLayout({
  children,
  navigation,
  activeScreen,
}: MainLayoutProps) {
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Header navigation={navigation} activeScreen={activeScreen} />
        <View style={styles.content}>{children}</View>
        <Footer />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    minHeight: 200,
  },
});