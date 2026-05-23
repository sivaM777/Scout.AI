import React, { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useNavigation } from "@react-navigation/native";
import { SafeAreaView } from "react-native-safe-area-context";
import { ProductUrlInput } from "../components/ProductUrlInput";
import { QuickActionCard } from "../components/QuickActionCard";
import { SectionCard } from "../components/SectionCard";
import { ActionButton } from "../components/ActionButton";
import { useShareIntent } from "../hooks/useShareIntent";
import { fetchHistory, fetchWatchlist } from "../services/api";
import { useAppState } from "../state/AppState";
import { theme } from "../theme";

const supportedLabels = ["Amazon", "Flipkart", "Ajio", "Myntra", "Nykaa", "Croma", "Reliance Digital", "and more"];

export function HomeScreen() {
  const navigation = useNavigation<any>();
  const { history, hydrateHistory, hydrateWatchlist, setCurrentReport } = useAppState();
  const [url, setUrl] = useState("");

  const startAnalysis = useCallback(
    (incomingUrl: string) => {
      if (!incomingUrl.trim()) {
        return;
      }

      navigation.navigate("Analyze", {
        url: incomingUrl.trim(),
      });
    },
    [navigation],
  );

  useShareIntent(startAnalysis);

  useEffect(() => {
    let isMounted = true;

    const hydrate = async () => {
      try {
        const [historyItems, watchlistItems] = await Promise.all([fetchHistory(), fetchWatchlist()]);
        if (!isMounted) {
          return;
        }

        hydrateHistory(historyItems);
        hydrateWatchlist(watchlistItems);
      } catch (error) {
        console.warn("HomeScreen hydration failed", error);
      }
    };

    void hydrate();

    return () => {
      isMounted = false;
    };
  }, [hydrateHistory, hydrateWatchlist]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.hero}>
          <View style={styles.heroBubble} />
          <Text style={styles.eyebrow}>AI shopping co-pilot</Text>
          <Text style={styles.title}>Share any product link and get a smarter buy-or-skip answer.</Text>
          <Text style={styles.subtitle}>
            Scout AI researches reviews, price context, and alternatives across marketplaces so you do not have to open five tabs before buying.
          </Text>
        </View>

        <ProductUrlInput value={url} onChangeText={setUrl} onSubmit={() => startAnalysis(url)} />

        <SectionCard title="Supported shopping sites" subtitle="Built as a multi-marketplace assistant, not a single-store tool.">
          <View style={styles.marketplaceRow}>
            {supportedLabels.map((label) => (
              <View key={label} style={styles.marketplaceChip}>
                <Text style={styles.marketplaceChipText}>{label}</Text>
              </View>
            ))}
          </View>
        </SectionCard>

        <View style={styles.horizontalSection}>
          <QuickActionCard
            eyebrow="Fast start"
            title="Share from any app"
            body="Open a product in any shopping app and send the link to Scout AI from Android share."
          />
          <QuickActionCard
            eyebrow="Safer decisions"
            title="See better alternatives"
            body="We surface stronger options when the current item is overpriced or too risky."
          />
          <QuickActionCard
            eyebrow="Stickiness"
            title="Track the right price"
            body="Save items to a watchlist and come back when the price finally makes sense."
          />
        </View>

        <SectionCard title="Recent research" subtitle="Your last reports stay one tap away.">
          {history.length === 0 ? (
            <Text style={styles.emptyText}>Your research history will show up here after the first scan.</Text>
          ) : (
            history.slice(0, 3).map((report) => (
              <View key={report.id} style={styles.historyRow}>
                <View style={styles.historyCopy}>
                  <Text style={styles.historyTitle}>{report.productName}</Text>
                  <Text style={styles.historyMeta}>
                    {report.marketplace} • {report.verdict.toUpperCase()} • Score {report.overallScore}
                  </Text>
                </View>
                <ActionButton
                  label="Open"
                  variant="secondary"
                  onPress={() => {
                    setCurrentReport(report);
                    navigation.navigate("Report");
                  }}
                  style={styles.inlineButton}
                />
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
    gap: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  hero: {
    backgroundColor: theme.colors.text,
    borderRadius: theme.radii.lg,
    padding: theme.spacing.xl,
    gap: theme.spacing.sm,
    overflow: "hidden",
  },
  heroBubble: {
    position: "absolute",
    top: -30,
    right: -20,
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: "rgba(198, 106, 58, 0.22)",
  },
  eyebrow: {
    color: "#CDEFE9",
    fontWeight: "700",
    fontSize: theme.typography.caption,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  title: {
    color: theme.colors.surface,
    fontSize: theme.typography.hero,
    lineHeight: 38,
    fontWeight: "800",
  },
  subtitle: {
    color: "#C8D3CD",
    fontSize: theme.typography.body,
    lineHeight: 22,
  },
  marketplaceRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: theme.spacing.sm,
  },
  marketplaceChip: {
    borderRadius: theme.radii.pill,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: theme.colors.surfaceMuted,
  },
  marketplaceChipText: {
    color: theme.colors.text,
    fontWeight: "600",
    fontSize: theme.typography.caption,
  },
  horizontalSection: {
    gap: theme.spacing.md,
  },
  emptyText: {
    color: theme.colors.textMuted,
    lineHeight: 20,
  },
  historyRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: theme.spacing.md,
  },
  historyCopy: {
    flex: 1,
    gap: 4,
  },
  historyTitle: {
    color: theme.colors.text,
    fontWeight: "700",
  },
  historyMeta: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.caption,
  },
  inlineButton: {
    minWidth: 92,
  },
});
