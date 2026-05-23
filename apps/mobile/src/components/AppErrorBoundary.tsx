import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { theme } from "../theme";

type AppErrorBoundaryState = {
  hasError: boolean;
};

export class AppErrorBoundary extends React.Component<React.PropsWithChildren, AppErrorBoundaryState> {
  state: AppErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(): AppErrorBoundaryState {
    return {
      hasError: true,
    };
  }

  componentDidCatch(error: unknown) {
    console.error("AppErrorBoundary caught an error", error);
  }

  private reset = () => {
    this.setState({
      hasError: false,
    });
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <View style={styles.screen}>
        <View style={styles.card}>
          <Text style={styles.eyebrow}>Scout AI</Text>
          <Text style={styles.title}>The app hit a startup problem.</Text>
          <Text style={styles.body}>
            Reopen the app once. If it still happens, connect the phone with USB debugging and we can pull the exact crash log.
          </Text>
          <Pressable style={styles.button} onPress={this.reset}>
            <Text style={styles.buttonText}>Try again</Text>
          </Pressable>
        </View>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.colors.background,
    padding: theme.spacing.lg,
  },
  card: {
    width: "100%",
    borderRadius: theme.radii.lg,
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.xl,
    gap: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  eyebrow: {
    color: theme.colors.accent,
    fontWeight: "700",
    fontSize: theme.typography.caption,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  title: {
    color: theme.colors.text,
    fontSize: 24,
    fontWeight: "800",
  },
  body: {
    color: theme.colors.textMuted,
    lineHeight: 22,
  },
  button: {
    alignSelf: "flex-start",
    backgroundColor: theme.colors.text,
    borderRadius: theme.radii.pill,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  buttonText: {
    color: theme.colors.surface,
    fontWeight: "700",
  },
});
