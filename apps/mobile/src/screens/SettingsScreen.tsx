import React from "react";
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from "react-native";
import { supportedMarketplaceOptions, type DealPreference, type MarketplaceSlug } from "@scout/shared";
import { SafeAreaView } from "react-native-safe-area-context";
import { SectionCard } from "../components/SectionCard";
import { useAppState } from "../state/AppState";
import { theme } from "../theme";

const dealPreferenceOptions: { value: DealPreference; label: string; body: string }[] = [
  {
    value: "aggressive",
    label: "Aggressive buy mode",
    body: "Scout will be more willing to call a deal good at slightly higher prices.",
  },
  {
    value: "balanced",
    label: "Balanced mode",
    body: "A middle ground between value hunting and convenience.",
  },
  {
    value: "conservative",
    label: "Conservative mode",
    body: "Scout waits for stronger discounts before calling something a good buy.",
  },
];

export function SettingsScreen() {
  const { settings, updateSettings } = useAppState();

  const updateToggle = (key: "compareAcrossMarketplaces" | "includeReddit" | "includeYouTube" | "includeEditorial" | "showPriceDeltaPercent", value: boolean) => {
    updateSettings({
      ...settings,
      [key]: value,
    });
  };

  const toggleMarketplace = (slug: MarketplaceSlug) => {
    if (settings.selectedMarketplaces.includes(slug)) {
      if (settings.selectedMarketplaces.length === 1) {
        return;
      }

      updateSettings({
        ...settings,
        selectedMarketplaces: settings.selectedMarketplaces.filter((item) => item !== slug),
      });
      return;
    }

    updateSettings({
      ...settings,
      selectedMarketplaces: [...settings.selectedMarketplaces, slug],
    });
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content}>
        <SectionCard title="Research controls" subtitle="These settings change the live report that Scout builds for each product.">
          <View style={styles.toggleRow}>
            <View style={styles.toggleCopy}>
              <Text style={styles.itemTitle}>Compare across marketplaces</Text>
              <Text style={styles.itemBody}>Look up live price matches across the stores you have enabled.</Text>
            </View>
            <Switch
              value={settings.compareAcrossMarketplaces}
              onValueChange={(value) => updateToggle("compareAcrossMarketplaces", value)}
              trackColor={{ false: theme.colors.border, true: theme.colors.accentSoft }}
              thumbColor={settings.compareAcrossMarketplaces ? theme.colors.accent : theme.colors.surface}
            />
          </View>

          <View style={styles.toggleRow}>
            <View style={styles.toggleCopy}>
              <Text style={styles.itemTitle}>Show percentage price deltas</Text>
              <Text style={styles.itemBody}>Display store-vs-store price gaps as percentages in the report.</Text>
            </View>
            <Switch
              value={settings.showPriceDeltaPercent}
              onValueChange={(value) => updateToggle("showPriceDeltaPercent", value)}
              trackColor={{ false: theme.colors.border, true: theme.colors.accentSoft }}
              thumbColor={settings.showPriceDeltaPercent ? theme.colors.accent : theme.colors.surface}
            />
          </View>
        </SectionCard>

        <SectionCard title="Source mix" subtitle="Choose which live evidence channels Scout should use.">
          <View style={styles.toggleRow}>
            <View style={styles.toggleCopy}>
              <Text style={styles.itemTitle}>Include Reddit threads</Text>
              <Text style={styles.itemBody}>Owner discussions are often the fastest way to catch recurring complaints.</Text>
            </View>
            <Switch
              value={settings.includeReddit}
              onValueChange={(value) => updateToggle("includeReddit", value)}
              trackColor={{ false: theme.colors.border, true: theme.colors.accentSoft }}
              thumbColor={settings.includeReddit ? theme.colors.accent : theme.colors.surface}
            />
          </View>

          <View style={styles.toggleRow}>
            <View style={styles.toggleCopy}>
              <Text style={styles.itemTitle}>Include YouTube transcripts</Text>
              <Text style={styles.itemBody}>Video reviews help with hands-on impressions, fit, and long-term usage notes.</Text>
            </View>
            <Switch
              value={settings.includeYouTube}
              onValueChange={(value) => updateToggle("includeYouTube", value)}
              trackColor={{ false: theme.colors.border, true: theme.colors.accentSoft }}
              thumbColor={settings.includeYouTube ? theme.colors.accent : theme.colors.surface}
            />
          </View>

          <View style={styles.toggleRow}>
            <View style={styles.toggleCopy}>
              <Text style={styles.itemTitle}>Include editorial search</Text>
              <Text style={styles.itemBody}>Keep broader comparison and issue-check searches in the final report.</Text>
            </View>
            <Switch
              value={settings.includeEditorial}
              onValueChange={(value) => updateToggle("includeEditorial", value)}
              trackColor={{ false: theme.colors.border, true: theme.colors.accentSoft }}
              thumbColor={settings.includeEditorial ? theme.colors.accent : theme.colors.surface}
            />
          </View>
        </SectionCard>

        <SectionCard title="Deal strictness" subtitle="Tune how fussy Scout should be before it calls a price good.">
          <View style={styles.preferenceStack}>
            {dealPreferenceOptions.map((option) => {
              const isSelected = settings.dealPreference === option.value;
              return (
                <Pressable
                  key={option.value}
                  onPress={() =>
                    updateSettings({
                      ...settings,
                      dealPreference: option.value,
                    })
                  }
                  style={[styles.preferenceCard, isSelected ? styles.preferenceCardSelected : null]}
                >
                  <Text style={styles.preferenceTitle}>{option.label}</Text>
                  <Text style={styles.preferenceBody}>{option.body}</Text>
                </Pressable>
              );
            })}
          </View>
        </SectionCard>

        <SectionCard title="Marketplace picker" subtitle="The same store list is also available under the search box before each research run.">
          <View style={styles.marketplaceRow}>
            {supportedMarketplaceOptions.map((option) => {
              const isSelected = settings.selectedMarketplaces.includes(option.slug);
              return (
                <Pressable
                  key={option.slug}
                  onPress={() => toggleMarketplace(option.slug)}
                  style={[styles.marketplaceChip, isSelected ? styles.marketplaceChipSelected : null]}
                >
                  <Text style={[styles.marketplaceChipText, isSelected ? styles.marketplaceChipTextSelected : null]}>
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
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
    gap: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  toggleRow: {
    flexDirection: "row",
    gap: theme.spacing.md,
    alignItems: "center",
    justifyContent: "space-between",
  },
  toggleCopy: {
    flex: 1,
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
  preferenceStack: {
    gap: theme.spacing.sm,
  },
  preferenceCard: {
    backgroundColor: theme.colors.surfaceMuted,
    borderRadius: theme.radii.md,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    gap: 6,
  },
  preferenceCardSelected: {
    backgroundColor: theme.colors.accentSoft,
    borderColor: theme.colors.accent,
  },
  preferenceTitle: {
    color: theme.colors.text,
    fontWeight: "800",
  },
  preferenceBody: {
    color: theme.colors.textMuted,
    lineHeight: 20,
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
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  marketplaceChipSelected: {
    backgroundColor: theme.colors.text,
    borderColor: theme.colors.text,
  },
  marketplaceChipText: {
    color: theme.colors.text,
    fontWeight: "700",
    fontSize: theme.typography.caption,
  },
  marketplaceChipTextSelected: {
    color: theme.colors.surface,
  },
});
