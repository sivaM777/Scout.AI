import React, { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { supportedMarketplaceOptions, type MarketplaceSlug } from "@scout/shared";
import { theme } from "../theme";

type ProductUrlInputProps = {
  value: string;
  onChangeText: (value: string) => void;
  onSubmit: () => void;
  selectedMarketplaces: MarketplaceSlug[];
  onChangeMarketplaces: (value: MarketplaceSlug[]) => void;
};

const popularMarketplaceSlugs: MarketplaceSlug[] = ["amazon", "flipkart", "ajio", "myntra", "nykaa", "croma"];

export function ProductUrlInput({
  value,
  onChangeText,
  onSubmit,
  selectedMarketplaces,
  onChangeMarketplaces,
}: ProductUrlInputProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const selectedCount = selectedMarketplaces.length;
  const selectedSet = useMemo(() => new Set(selectedMarketplaces), [selectedMarketplaces]);

  const toggleMarketplace = (slug: MarketplaceSlug) => {
    if (selectedSet.has(slug)) {
      if (selectedCount === 1) {
        return;
      }

      onChangeMarketplaces(selectedMarketplaces.filter((item) => item !== slug));
      return;
    }

    onChangeMarketplaces([...selectedMarketplaces, slug]);
  };

  return (
    <View style={styles.wrapper}>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder="Paste any product link from Amazon, Flipkart, Ajio, Myntra, Nykaa and more"
        placeholderTextColor={theme.colors.textMuted}
        style={styles.input}
        autoCapitalize="none"
        autoCorrect={false}
      />
      <Pressable onPress={() => setIsExpanded((current) => !current)} style={styles.dropdownBar}>
        <View style={styles.dropdownCopy}>
          <Text style={styles.dropdownLabel}>Compare stores</Text>
          <Text style={styles.dropdownValue}>{selectedCount} selected for live price comparison</Text>
        </View>
        <Text style={styles.dropdownChevron}>{isExpanded ? "Hide" : "Choose"}</Text>
      </Pressable>
      {isExpanded ? (
        <View style={styles.dropdownPanel}>
          <View style={styles.quickRow}>
            <Pressable
              onPress={() => onChangeMarketplaces(supportedMarketplaceOptions.map((option) => option.slug))}
              style={styles.quickChip}
            >
              <Text style={styles.quickChipText}>Select all</Text>
            </Pressable>
            <Pressable onPress={() => onChangeMarketplaces(popularMarketplaceSlugs)} style={styles.quickChip}>
              <Text style={styles.quickChipText}>Popular 6</Text>
            </Pressable>
          </View>
          <View style={styles.marketplaceGrid}>
            {supportedMarketplaceOptions.map((option) => {
              const isSelected = selectedSet.has(option.slug);

              return (
                <Pressable
                  key={option.slug}
                  onPress={() => toggleMarketplace(option.slug)}
                  style={[styles.marketplaceChip, isSelected ? styles.marketplaceChipSelected : styles.marketplaceChipIdle]}
                >
                  <Text style={[styles.marketplaceChipText, isSelected ? styles.marketplaceChipTextSelected : null]}>
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      ) : null}
      <Pressable onPress={onSubmit} style={styles.button}>
        <Text style={styles.buttonText}>Research</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radii.lg,
    padding: theme.spacing.sm,
    borderWidth: 1,
    borderColor: theme.colors.border,
    gap: theme.spacing.sm,
    ...theme.shadow.card,
  },
  input: {
    minHeight: 90,
    borderRadius: theme.radii.md,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.surfaceMuted,
    color: theme.colors.text,
    textAlignVertical: "top",
  },
  dropdownBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    borderRadius: theme.radii.md,
    backgroundColor: theme.colors.surfaceMuted,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  dropdownCopy: {
    flex: 1,
    gap: 2,
  },
  dropdownLabel: {
    color: theme.colors.text,
    fontWeight: "700",
  },
  dropdownValue: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.caption,
  },
  dropdownChevron: {
    color: theme.colors.accent,
    fontWeight: "700",
  },
  dropdownPanel: {
    gap: theme.spacing.md,
    padding: theme.spacing.md,
    borderRadius: theme.radii.md,
    backgroundColor: "#FCFAF5",
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  quickRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: theme.spacing.sm,
  },
  quickChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: theme.radii.pill,
    backgroundColor: theme.colors.accentSoft,
  },
  quickChipText: {
    color: theme.colors.accent,
    fontWeight: "700",
    fontSize: theme.typography.caption,
  },
  marketplaceGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: theme.spacing.sm,
  },
  marketplaceChip: {
    borderRadius: theme.radii.pill,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
  },
  marketplaceChipSelected: {
    backgroundColor: theme.colors.text,
    borderColor: theme.colors.text,
  },
  marketplaceChipIdle: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
  },
  marketplaceChipText: {
    fontWeight: "700",
    fontSize: theme.typography.caption,
  },
  marketplaceChipTextSelected: {
    color: theme.colors.surface,
  },
  button: {
    alignSelf: "flex-start",
    backgroundColor: theme.colors.warm,
    borderRadius: theme.radii.pill,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: 12,
  },
  buttonText: {
    color: theme.colors.surface,
    fontWeight: "700",
  },
});
