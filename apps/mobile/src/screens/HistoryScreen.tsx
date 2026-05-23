import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { ActionButton } from "../components/ActionButton";
import { SectionCard } from "../components/SectionCard";
import { useAppState } from "../state/AppState";
import { theme } from "../theme";

export function HistoryScreen() {
  const navigation = useNavigation<any>();
  const { history, setCurrentReport } = useAppState();

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content}>
        <SectionCard title="Research history" subtitle="Reports are kept here so users can come back before checkout.">
          {history.length === 0 ? (
            <Text style={styles.emptyText}>No reports yet. Start from Home and analyze your first product.</Text>
          ) : (
            history.map((report) => (
              <View key={report.id} style={styles.row}>
                <View style={styles.copy}>
                  <Text style={styles.title}>{report.productName}</Text>
                  <Text style={styles.meta}>
                    {report.marketplace} • {report.productCategory} • Score {report.overallScore}
                  </Text>
                </View>
                <ActionButton
                  label="View"
                  variant="secondary"
                  onPress={() => {
                    setCurrentReport(report);
                    navigation.navigate("Report");
                  }}
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
  },
  emptyText: {
    color: theme.colors.textMuted,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: theme.spacing.md,
  },
  copy: {
    flex: 1,
    gap: 4,
  },
  title: {
    color: theme.colors.text,
    fontWeight: "700",
  },
  meta: {
    color: theme.colors.textMuted,
    fontSize: theme.typography.caption,
  },
});
