import React from "react";
import { Text, View } from "react-native";
import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { HomeScreen } from "../screens/HomeScreen";
import { AnalyzeScreen } from "../screens/AnalyzeScreen";
import { ReportScreen } from "../screens/ReportScreen";
import { HistoryScreen } from "../screens/HistoryScreen";
import { WatchlistScreen } from "../screens/WatchlistScreen";
import { SettingsScreen } from "../screens/SettingsScreen";
import { theme } from "../theme";

export type RootStackParamList = {
  MainTabs: undefined;
  Analyze: { url: string; sourceApp?: string };
  Report: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

function TabGlyph({ label, focused }: { label: string; focused: boolean }) {
  return (
    <View
      style={{
        width: 26,
        height: 26,
        borderRadius: 13,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: focused ? theme.colors.accent : theme.colors.surfaceMuted,
      }}
    >
      <Text style={{ color: focused ? theme.colors.surface : theme.colors.textMuted, fontWeight: "700" }}>
        {label}
      </Text>
    </View>
  );
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.background,
        },
        headerShadowVisible: false,
        headerTintColor: theme.colors.text,
        headerTitleStyle: {
          fontWeight: "700",
        },
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
          height: 74,
          paddingBottom: 10,
          paddingTop: 8,
        },
        tabBarActiveTintColor: theme.colors.text,
        tabBarInactiveTintColor: theme.colors.textMuted,
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabGlyph focused={focused} label="H" />,
        }}
      />
      <Tab.Screen
        name="History"
        component={HistoryScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabGlyph focused={focused} label="R" />,
        }}
      />
      <Tab.Screen
        name="Watchlist"
        component={WatchlistScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabGlyph focused={focused} label="W" />,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabGlyph focused={focused} label="S" />,
        }}
      />
    </Tab.Navigator>
  );
}

const navigationTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: theme.colors.background,
    card: theme.colors.surface,
    border: theme.colors.border,
    primary: theme.colors.accent,
    text: theme.colors.text,
  },
};

export function AppNavigator() {
  return (
    <NavigationContainer theme={navigationTheme}>
      <Stack.Navigator>
        <Stack.Screen name="MainTabs" component={MainTabs} options={{ headerShown: false }} />
        <Stack.Screen
          name="Analyze"
          component={AnalyzeScreen}
          options={{
            title: "Researching",
            headerStyle: {
              backgroundColor: theme.colors.background,
            },
            headerShadowVisible: false,
          }}
        />
        <Stack.Screen
          name="Report"
          component={ReportScreen}
          options={{
            title: "Scout Report",
            headerStyle: {
              backgroundColor: theme.colors.background,
            },
            headerShadowVisible: false,
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
