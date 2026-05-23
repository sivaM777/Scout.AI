import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { SectionCard } from "../components/SectionCard";
import { useAppState } from "../state/AppState";
import { theme } from "../theme";

export function WatchlistScreen() {
  const { watchlist } = useAppState();

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content}>
        <SectionCard title="Watchlist" subtitle="A small retention feature that makes the app useful before and after the first report.">
          {watchlist.length === 0 ? (
            <Text style={styles.emptyText}>Track price from any report and your saved items will appear here.</Text>
          ) : (
            watchlist.map((item) => (
              <View key={item.id} style={styles.row}>
                <View style={styles.copy}>
                  <Text style={styles.title}>{item.productName}</Text>
                  <Text style={styles.meta}>
                    Current {item.currency} {item.currentPrice.toFixed(0)}
                    {item.targetPrice ? ` • Target ${item.targetPrice.toFixed(0)}` : ""}
                  </Text>
                  {item.note ? <Text style={styles.note}>{item.note}</Text> : null}
                </View>
              </View>
            ))
          )}
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
  emptyText: {
    color: theme.colors.textMuted,
  },
  row: {
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  copy: {
    gap: 4,
  },
  title: {
    color: theme.colors.text,
    fontWeight: "700",
  },
  meta: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.caption,
  },
  note: {
    color: theme.colors.text,
    lineHeight: 20,
  },
});
