import React, { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { SafeAreaView } from "react-native-safe-area-context";
import { ProgressTimeline } from "../components/ProgressTimeline";
import { analyzeProductLink } from "../services/api";
import { useAppState } from "../state/AppState";
import { theme } from "../theme";
import type { RootStackParamList } from "../navigation/AppNavigator";

const steps = [
  "Reading the product link and identifying the marketplace",
  "Collecting community and editorial review signals",
  "Estimating price quality and live cross-store pricing",
  "Drafting a final buy, wait, or skip verdict",
];

export function AnalyzeScreen({ route, navigation }: NativeStackScreenProps<RootStackParamList, "Analyze">) {
  const { setCurrentReport, settings } = useAppState();
  const [activeIndex, setActiveIndex] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const productUrl = route.params.url;

  const hostLabel = useMemo(() => {
    try {
      return new URL(productUrl).hostname.replace("www.", "");
    } catch {
      return "shared link";
    }
  }, [productUrl]);

  useEffect(() => {
    let isMounted = true;

    const progressTimer = setInterval(() => {
      setActiveIndex((current) => Math.min(current + 1, steps.length - 1));
    }, 1300);

    void analyzeProductLink({
      url: productUrl,
      sourceApp: hostLabel,
      preferences: settings,
    })
      .then((report) => {
        if (!isMounted) {
          return;
        }

        clearInterval(progressTimer);
        setCurrentReport(report);
        navigation.replace("Report");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }

        clearInterval(progressTimer);
        setErrorMessage(error instanceof Error ? error.message : "Live research failed.");
      });

    return () => {
      isMounted = false;
      clearInterval(progressTimer);
    };
  }, [hostLabel, navigation, productUrl, setCurrentReport, settings]);

  if (errorMessage) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.content}>
          <View style={styles.heroCard}>
            <Text style={styles.eyebrow}>Live research failed</Text>
            <Text style={styles.title}>Scout could not fetch real-time data for this product.</Text>
            <Text style={styles.subtitle}>
              {errorMessage}. Check the link or backend connection and try again. We do not show mock reports here.
            </Text>
          </View>

          <View style={styles.statusCard}>
            <Text style={styles.statusHeadline}>Try again after a few seconds</Text>
            <Text style={styles.statusBody}>
              Some stores rate-limit scraping or the backend may be waking up from idle. A retry is better than trusting fake demo data.
            </Text>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.content}>
        <View style={styles.heroCard}>
          <Text style={styles.eyebrow}>Analyzing</Text>
          <Text style={styles.title}>We're building a shopping brief for this item.</Text>
          <Text style={styles.subtitle}>
            Marketplace detected: {hostLabel}. Scout AI is checking product signals, price quality, and {settings.selectedMarketplaces.length} selected comparison stores.
          </Text>
        </View>

        <View style={styles.statusCard}>
          <ActivityIndicator color={theme.colors.accent} size="large" />
          <Text style={styles.statusHeadline}>Working through the research steps</Text>
          <Text style={styles.statusBody}>
            Cached products will feel instant. New products may take longer while the intelligence service assembles real source evidence and live marketplace prices.
          </Text>
          <ProgressTimeline steps={steps} activeIndex={activeIndex} />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    flex: 1,
    padding: theme.spacing.lg,
    gap: theme.spacing.lg,
  },
  heroCard: {
    backgroundColor: theme.colors.text,
    borderRadius: theme.radii.lg,
    padding: theme.spacing.xl,
    gap: theme.spacing.sm,
  },
  eyebrow: {
    color: "#BDE4DE",
    fontWeight: "700",
    textTransform: "uppercase",
    fontSize: theme.typography.caption,
  },
  title: {
    color: theme.colors.surface,
    fontSize: theme.typography.title,
    fontWeight: "800",
    lineHeight: 30,
  },
  subtitle: {
    color: "#C5D4CF",
    lineHeight: 22,
  },
  statusCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radii.lg,
    padding: theme.spacing.xl,
    gap: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    ...theme.shadow.card,
  },
  statusHeadline: {
    color: theme.colors.text,
    fontSize: theme.typography.subtitle,
    fontWeight: "700",
  },
  statusBody: {
    color: theme.colors.textMuted,
    lineHeight: 20,
  },
});
