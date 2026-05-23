import React from "react";
import { StyleSheet, Text, View } from "react-native";
import type { PricePoint } from "@scout/shared";
import { theme } from "../theme";

type PriceHistoryMiniChartProps = {
  history: PricePoint[];
};

export function PriceHistoryMiniChart({ history }: PriceHistoryMiniChartProps) {
  const maxValue = Math.max(...history.map((point) => point.value), 1);

  return (
    <View style={styles.wrapper}>
      {history.map((point) => (
        <View key={point.label} style={styles.column}>
          <View style={styles.track}>
            <View
              style={[
                styles.fill,
                {
                  height: `${Math.max((point.value / maxValue) * 100, 18)}%`,
                },
              ]}
            />
          </View>
          <Text style={styles.label}>{point.label}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: theme.spacing.sm,
  },
  column: {
    flex: 1,
    alignItems: "center",
    gap: theme.spacing.xs,
  },
  track: {
    width: "100%",
    height: 90,
    justifyContent: "flex-end",
    backgroundColor: theme.colors.surfaceMuted,
    borderRadius: theme.radii.md,
    overflow: "hidden",
  },
  fill: {
    width: "100%",
    backgroundColor: theme.colors.accent,
    borderRadius: theme.radii.md,
  },
  label: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.tiny,
  },
});
