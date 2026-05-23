import React from "react";
import { StatusBar } from "react-native";
import { AppErrorBoundary } from "./components/AppErrorBoundary";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { AppNavigator } from "./navigation/AppNavigator";
import { AppStateProvider } from "./state/AppState";
import { theme } from "./theme";

export default function App() {
  return (
    <AppErrorBoundary>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <SafeAreaProvider>
          <AppStateProvider>
            <StatusBar barStyle="dark-content" backgroundColor={theme.colors.background} />
            <AppNavigator />
          </AppStateProvider>
        </SafeAreaProvider>
      </GestureHandlerRootView>
    </AppErrorBoundary>
  );
}
