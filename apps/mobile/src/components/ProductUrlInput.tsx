import React from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { theme } from "../theme";

type ProductUrlInputProps = {
  value: string;
  onChangeText: (value: string) => void;
  onSubmit: () => void;
};

export function ProductUrlInput({ value, onChangeText, onSubmit }: ProductUrlInputProps) {
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
