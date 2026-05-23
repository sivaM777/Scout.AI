import React from "react";
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { ActionButton } from "../components/ActionButton";
import { PriceHistoryMiniChart } from "../components/PriceHistoryMiniChart";
import { ScoreRing } from "../components/ScoreRing";
import { SectionCard } from "../components/SectionCard";
import { SourceList } from "../components/SourceList";
import { createWatchlistItem } from "../services/api";
import { useAppState } from "../state/AppState";
import { theme } from "../theme";

function formatPrice(value: number | null, currency: string) {
  if (value === null) {
    return "Unavailable";
  }

  const prefix = currency === "USD" ? "$" : "Rs ";
  return `${prefix}${value.toFixed(0)}`;
}

function formatDelta(value: number | null, percent: number | null, showPercent: boolean) {
  if (value === null) {
    return "No live price found";
  }

  if (showPercent && percent !== null) {
    const sign = percent > 0 ? "+" : "";
    return `${sign}${percent.toFixed(2)}% vs current`;
  }

  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(0)} vs current`;
}

function priceSourceLabel(source: "live" | "historical" | "estimated") {
  if (source === "live") {
    return "Live listing price";
  }
  if (source === "historical") {
    return "Last recorded live price";
  }
  return "Estimated fallback price";
}

export function ReportScreen() {
  const { currentReport, addWatchlistItem, settings } = useAppState();

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

  const reviewSources = currentReport.sources.filter((source) => source.sourceType === "reddit" || source.sourceType === "youtube");
  const supportingSources = currentReport.sources.filter((source) => source.sourceType !== "reddit" && source.sourceType !== "youtube");

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

        <SectionCard
          title="Live marketplace prices"
          subtitle={`${currentReport.pricing.marketplacePrices.length} stores checked from your selected list`}
        >
          {currentReport.pricing.marketplacePrices.length === 0 ? (
            <Text style={styles.bodyText}>Marketplace comparison is disabled for this run or no stores were selected.</Text>
          ) : (
          <View style={styles.comparisonStack}>
            {currentReport.pricing.marketplacePrices.map((entry) => {
              const content = (
                <>
                  <View style={styles.comparisonCopy}>
                    <Text style={styles.comparisonTitle}>{entry.marketplaceLabel}</Text>
                    <Text style={styles.comparisonBody}>{entry.productName}</Text>
                    <Text style={styles.comparisonMeta}>{entry.note ?? (entry.isOriginalListing ? "Current listing" : "Live matched listing")}</Text>
                  </View>
                  <View style={styles.comparisonValueBlock}>
                    <Text style={styles.comparisonPrice}>{formatPrice(entry.currentPrice, entry.currency)}</Text>
                    <Text
                      style={[
                        styles.comparisonDelta,
                        entry.priceStatus === "cheaper"
                          ? styles.cheaperText
                          : entry.priceStatus === "higher"
                            ? styles.higherText
                            : styles.neutralText,
                      ]}
                    >
                      {entry.isOriginalListing
                        ? "Current listing"
                        : formatDelta(entry.differenceAmount, entry.differencePercent, settings.showPriceDeltaPercent)}
                    </Text>
                  </View>
                </>
              );

              const productUrl = entry.productUrl;

              if (productUrl) {
                return (
                  <Pressable key={`${entry.marketplaceSlug}-${entry.productName}`} onPress={() => void Linking.openURL(productUrl)} style={styles.comparisonRow}>
                    {content}
                  </Pressable>
                );
              }

              return (
                <View key={`${entry.marketplaceSlug}-${entry.productName}`} style={styles.comparisonRow}>
                  {content}
                </View>
              );
            })}
          </View>
          )}
        </SectionCard>

        <SectionCard
          title="Price intelligence"
          subtitle={`${priceSourceLabel(currentReport.pricing.priceSource)}: ${formatPrice(currentReport.pricing.currentPrice, currentReport.pricing.currency)}`}
        >
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
              - {pro}
            </Text>
          ))}
        </SectionCard>

        <SectionCard title="Watch-outs">
          {currentReport.cons.map((con) => (
            <Text key={con} style={styles.listItem}>
              - {con}
            </Text>
          ))}
        </SectionCard>

        <SectionCard title="Community pulse" subtitle="Plain-language signal">
          <Text style={styles.bodyText}>{currentReport.communityPulse}</Text>
        </SectionCard>

        <SectionCard title="Live review evidence" subtitle="Reddit and YouTube signals used in the verdict">
          {reviewSources.length > 0 ? (
            <SourceList sources={reviewSources} />
          ) : (
            <Text style={styles.bodyText}>No live Reddit or YouTube review evidence was available for this run.</Text>
          )}
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

        <SectionCard title="Source transparency" subtitle="Editorial, comparison, and listing context">
          {supportingSources.length > 0 ? (
            <SourceList sources={supportingSources} />
          ) : (
            <Text style={styles.bodyText}>No extra editorial or listing sources were attached to this report.</Text>
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
  comparisonStack: {
    gap: theme.spacing.sm,
  },
  comparisonRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: theme.spacing.md,
    justifyContent: "space-between",
    backgroundColor: theme.colors.surfaceMuted,
    borderRadius: theme.radii.md,
    padding: theme.spacing.md,
  },
  comparisonCopy: {
    flex: 1,
    gap: 4,
  },
  comparisonTitle: {
    color: theme.colors.text,
    fontWeight: "800",
  },
  comparisonBody: {
    color: theme.colors.text,
    lineHeight: 20,
  },
  comparisonMeta: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.caption,
  },
  comparisonValueBlock: {
    alignItems: "flex-end",
    gap: 4,
  },
  comparisonPrice: {
    color: theme.colors.text,
    fontWeight: "800",
    fontSize: theme.typography.subtitle,
  },
  comparisonDelta: {
    fontSize: theme.typography.caption,
    fontWeight: "700",
  },
  cheaperText: {
    color: theme.colors.success,
  },
  higherText: {
    color: theme.colors.danger,
  },
  neutralText: {
    color: theme.colors.textMuted,
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
