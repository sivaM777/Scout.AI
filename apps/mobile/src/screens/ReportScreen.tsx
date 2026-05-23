import React from "react";
import { Linking, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { ActionButton } from "../components/ActionButton";
import { PriceHistoryMiniChart } from "../components/PriceHistoryMiniChart";
import { ScoreRing } from "../components/ScoreRing";
import { SectionCard } from "../components/SectionCard";
import { SourceList } from "../components/SourceList";
import { createWatchlistItem } from "../services/api";
import { useAppState } from "../state/AppState";
import { theme } from "../theme";

export function ReportScreen() {
  const { currentReport, addWatchlistItem } = useAppState();

  if (!currentReport) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>No active report yet</Text>
          <Text style={styles.emptyBody}>Start from Home and share or paste a shopping link to generate a report.</Text>
        </View>
      </SafeAreaView>
    );
  }

  const verdictTone =
    currentReport.verdict === "buy"
      ? styles.buyTone
      : currentReport.verdict === "wait"
        ? styles.waitTone
        : styles.skipTone;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={[styles.heroCard, verdictTone]}>
          <View style={styles.heroTopRow}>
            <ScoreRing score={currentReport.overallScore} verdict={currentReport.verdict} />
            <View style={styles.heroCopy}>
              <Text style={styles.marketplace}>{currentReport.marketplace}</Text>
              <Text style={styles.productName}>{currentReport.productName}</Text>
              <Text style={styles.summary}>{currentReport.oneLineSummary}</Text>
              <Text style={styles.confidence}>Confidence {currentReport.confidence}%</Text>
            </View>
          </View>
          <View style={styles.buttonRow}>
            <ActionButton
              label="Open listing"
              onPress={() => void Linking.openURL(currentReport.productUrl)}
              style={styles.flexButton}
            />
            <ActionButton
              label="Track price"
              variant="secondary"
              onPress={() => {
                void createWatchlistItem({
                  productName: currentReport.productName,
                  productUrl: currentReport.productUrl,
                  currentPrice: currentReport.pricing.currentPrice,
                  currency: currentReport.pricing.currency,
                  targetPrice: currentReport.pricing.recommendedTargetPrice,
                  note: "Added from Scout report.",
                }).then(addWatchlistItem);
              }}
              style={styles.flexButton}
            />
          </View>
        </View>

        <SectionCard title="Verdict reason" subtitle={currentReport.verdict.toUpperCase()}>
          <Text style={styles.bodyText}>{currentReport.verdictReason}</Text>
        </SectionCard>

        <SectionCard title="Price intelligence" subtitle={`Current ${currentReport.pricing.currency} ${currentReport.pricing.currentPrice.toFixed(0)}`}>
          <View style={styles.priceGrid}>
            <View style={styles.metricPill}>
              <Text style={styles.metricLabel}>Average</Text>
              <Text style={styles.metricValue}>{currentReport.pricing.averagePrice.toFixed(0)}</Text>
            </View>
            <View style={styles.metricPill}>
              <Text style={styles.metricLabel}>Lowest</Text>
              <Text style={styles.metricValue}>{currentReport.pricing.lowestPrice.toFixed(0)}</Text>
            </View>
            <View style={styles.metricPill}>
              <Text style={styles.metricLabel}>Target</Text>
              <Text style={styles.metricValue}>{currentReport.pricing.recommendedTargetPrice.toFixed(0)}</Text>
            </View>
          </View>
          <PriceHistoryMiniChart history={currentReport.pricing.history} />
        </SectionCard>

        <SectionCard title="What works well">
          {currentReport.pros.map((pro) => (
            <Text key={pro} style={styles.listItem}>
              • {pro}
            </Text>
          ))}
        </SectionCard>

        <SectionCard title="Watch-outs">
          {currentReport.cons.map((con) => (
            <Text key={con} style={styles.listItem}>
              • {con}
            </Text>
          ))}
        </SectionCard>

        <SectionCard title="Community pulse" subtitle="Plain-language signal">
          <Text style={styles.bodyText}>{currentReport.communityPulse}</Text>
        </SectionCard>

        <SectionCard title="Alternative picks" subtitle="Extra feature for safer decisions">
          {currentReport.alternatives.map((alternative) => (
            <View key={alternative.id} style={styles.alternativeRow}>
              <View style={styles.alternativeCopy}>
                <Text style={styles.alternativeTitle}>{alternative.name}</Text>
                <Text style={styles.alternativeReason}>{alternative.reason}</Text>
              </View>
              <View style={styles.alternativePriceTag}>
                <Text style={styles.alternativePriceText}>{alternative.estimatedPrice.toFixed(0)}</Text>
              </View>
            </View>
          ))}
        </SectionCard>

        <SectionCard title="Source transparency" subtitle="Tap any card to inspect the source search result">
          <SourceList sources={currentReport.sources} />
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
  emptyState: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: theme.spacing.xl,
  },
  emptyTitle: {
    fontSize: theme.typography.title,
    fontWeight: "800",
    color: theme.colors.text,
  },
  emptyBody: {
    color: theme.colors.textMuted,
    textAlign: "center",
    marginTop: theme.spacing.sm,
  },
  heroCard: {
    borderRadius: theme.radii.lg,
    padding: theme.spacing.xl,
    gap: theme.spacing.lg,
    ...theme.shadow.card,
  },
  heroTopRow: {
    flexDirection: "row",
    gap: theme.spacing.lg,
  },
  heroCopy: {
    flex: 1,
    gap: theme.spacing.xs,
  },
  marketplace: {
    color: theme.colors.textMuted,
    fontWeight: "700",
    textTransform: "uppercase",
    fontSize: theme.typography.caption,
  },
  productName: {
    color: theme.colors.text,
    fontSize: theme.typography.title,
    fontWeight: "800",
    lineHeight: 30,
  },
  summary: {
    color: theme.colors.text,
    lineHeight: 22,
  },
  confidence: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.caption,
  },
  buttonRow: {
    flexDirection: "row",
    gap: theme.spacing.sm,
  },
  flexButton: {
    flex: 1,
  },
  buyTone: {
    backgroundColor: "#E8F5EE",
  },
  waitTone: {
    backgroundColor: "#F8EED0",
  },
  skipTone: {
    backgroundColor: "#F7E0DE",
  },
  bodyText: {
    color: theme.colors.text,
    lineHeight: 22,
  },
  priceGrid: {
    flexDirection: "row",
    gap: theme.spacing.sm,
  },
  metricPill: {
    flex: 1,
    backgroundColor: theme.colors.surfaceMuted,
    borderRadius: theme.radii.md,
    padding: theme.spacing.md,
    gap: 4,
  },
  metricLabel: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.caption,
  },
  metricValue: {
    color: theme.colors.text,
    fontSize: theme.typography.subtitle,
    fontWeight: "700",
  },
  listItem: {
    color: theme.colors.text,
    lineHeight: 22,
  },
  alternativeRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: theme.spacing.md,
    backgroundColor: theme.colors.surfaceMuted,
    borderRadius: theme.radii.md,
    padding: theme.spacing.md,
  },
  alternativeCopy: {
    flex: 1,
    gap: 4,
  },
  alternativeTitle: {
    color: theme.colors.text,
    fontWeight: "700",
  },
  alternativeReason: {
    color: theme.colors.textMuted,
    lineHeight: 20,
  },
  alternativePriceTag: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radii.pill,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  alternativePriceText: {
    color: theme.colors.text,
    fontWeight: "700",
  },
});
