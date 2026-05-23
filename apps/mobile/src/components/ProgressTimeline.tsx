import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { theme } from "../theme";

type ProgressTimelineProps = {
  steps: string[];
  activeIndex: number;
};

export function ProgressTimeline({ steps, activeIndex }: ProgressTimelineProps) {
  return (
    <View style={styles.wrapper}>
      {steps.map((step, index) => {
        const state = index < activeIndex ? "done" : index === activeIndex ? "active" : "idle";

        return (
          <View key={step} style={styles.row}>
            <View
              style={[
                styles.dot,
                state === "done"
                  ? styles.doneDot
                  : state === "active"
                    ? styles.activeDot
                    : styles.idleDot,
              ]}
            />
            <Text
              style={[
                styles.label,
                state === "active" ? styles.activeLabel : state === "done" ? styles.doneLabel : undefined,
              ]}
            >
              {step}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    gap: theme.spacing.md,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: theme.spacing.sm,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  doneDot: {
    backgroundColor: theme.colors.success,
  },
  activeDot: {
    backgroundColor: theme.colors.warm,
  },
  idleDot: {
    backgroundColor: theme.colors.border,
  },
  label: {
    color: theme.colors.textMuted,
  },
  activeLabel: {
    color: theme.colors.text,
    fontWeight: "700",
  },
  doneLabel: {
    color: theme.colors.text,
  },
});
