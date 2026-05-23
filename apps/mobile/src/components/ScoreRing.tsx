import React from "react";
import { StyleSheet, Text, View } from "react-native";
import type { Verdict } from "@scout/shared";
import { theme } from "../theme";

type ScoreRingProps = {
  score: number;
  verdict: Verdict;
};

export function ScoreRing({ score, verdict }: ScoreRingProps) {
  const borderColor =
    verdict === "buy"
      ? theme.colors.success
      : verdict === "wait"
        ? theme.colors.warning
        : theme.colors.danger;

  return (
    <View style={[styles.outer, { borderColor }]}>
      <View style={styles.inner}>
        <Text style={styles.score}>{score}</Text>
        <Text style={styles.label}>Score</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 10,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: theme.colors.surfaceMuted,
  },
  inner: {
    alignItems: "center",
    gap: 2,
  },
  score: {
    fontSize: 34,
    fontWeight: "800",
    color: theme.colors.text,
  },
  label: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.caption,
  },
});
