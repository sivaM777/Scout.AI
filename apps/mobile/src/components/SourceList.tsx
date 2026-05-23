import React from "react";
import { Linking, Pressable, StyleSheet, Text, View } from "react-native";
import type { SourceEvidence } from "@scout/shared";
import { theme } from "../theme";

type SourceListProps = {
  sources: SourceEvidence[];
};

export function SourceList({ sources }: SourceListProps) {
  return (
    <View style={styles.wrapper}>
      {sources.map((source) => (
        <Pressable key={source.id} onPress={() => void Linking.openURL(source.url)} style={styles.card}>
          <View style={styles.row}>
            <Text style={styles.title}>{source.title}</Text>
            <View
              style={[
                styles.sentimentBadge,
                source.sentiment === "positive"
                  ? styles.positiveBadge
                  : source.sentiment === "mixed"
                    ? styles.mixedBadge
                    : styles.negativeBadge,
              ]}
            >
              <Text style={styles.sentimentText}>{source.sentiment}</Text>
            </View>
          </View>
          <Text style={styles.summary}>{source.summary}</Text>
          {source.snippet ? <Text style={styles.snippet}>"{source.snippet}"</Text> : null}
          <Text style={styles.meta}>
            {[source.trustLabel, source.sourceType, source.domain, source.evidenceCount ? `${source.evidenceCount} signals` : null]
              .filter(Boolean)
              .join(" - ")}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    gap: theme.spacing.md,
  },
  card: {
    padding: theme.spacing.md,
    borderRadius: theme.radii.md,
    backgroundColor: theme.colors.surfaceMuted,
    gap: theme.spacing.sm,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: theme.spacing.sm,
  },
  title: {
    flex: 1,
    color: theme.colors.text,
    fontWeight: "700",
  },
  summary: {
    color: theme.colors.textMuted,
    lineHeight: 20,
  },
  snippet: {
    color: theme.colors.text,
    lineHeight: 20,
    fontStyle: "italic",
  },
  meta: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.tiny,
  },
  sentimentBadge: {
    borderRadius: theme.radii.pill,
    paddingHorizontal: 10,
    paddingVertical: 6,
    alignSelf: "flex-start",
  },
  positiveBadge: {
    backgroundColor: "#DBF5E6",
  },
  mixedBadge: {
    backgroundColor: "#F7E9BF",
  },
  negativeBadge: {
    backgroundColor: "#F7D8D5",
  },
  sentimentText: {
    textTransform: "capitalize",
    color: theme.colors.text,
    fontSize: theme.typography.tiny,
    fontWeight: "700",
  },
});
