import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { SectionCard } from "../components/SectionCard";
import { theme } from "../theme";

export function SettingsScreen() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content}>
        <SectionCard title="Product direction" subtitle="These blocks explain how the app is positioned for users.">
          <View style={styles.stack}>
            <Text style={styles.itemTitle}>Universal shopping support</Text>
            <Text style={styles.itemBody}>The backend is designed around a marketplace registry so new sites can be added without rebuilding the app.</Text>
          </View>
          <View style={styles.stack}>
            <Text style={styles.itemTitle}>Source transparency</Text>
            <Text style={styles.itemBody}>Every verdict is paired with visible evidence cards so users trust the recommendation.</Text>
          </View>
          <View style={styles.stack}>
            <Text style={styles.itemTitle}>Retention hooks</Text>
            <Text style={styles.itemBody}>History, watchlist, and alternatives make the app useful beyond a single one-off lookup.</Text>
          </View>
        </SectionCard>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    padding: theme.spacing.lg,
  },
  stack: {
    gap: 6,
  },
  itemTitle: {
    color: theme.colors.text,
    fontWeight: "700",
  },
  itemBody: {
    color: theme.colors.textMuted,
    lineHeight: 20,
  },
});
