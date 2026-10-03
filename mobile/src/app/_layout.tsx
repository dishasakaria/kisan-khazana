import { Inter_400Regular, Inter_600SemiBold, Inter_700Bold, useFonts } from "@expo-google-fonts/inter";
import { Mukta_400Regular, Mukta_600SemiBold, Mukta_700Bold } from "@expo-google-fonts/mukta";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { StatusBar } from "expo-status-bar";
import { useEffect } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { SessionProvider, useSession } from "@/lib/session";
import { C } from "@/lib/theme";

SplashScreen.preventAutoHideAsync().catch(() => {});

function Root() {
  const { ready, token, t, lang } = useSession();
  const [fonts, fontErr] = useFonts({ Inter_400Regular, Inter_600SemiBold, Inter_700Bold, Mukta_400Regular, Mukta_600SemiBold, Mukta_700Bold });
  const loaded = ready && (fonts || !!fontErr);
  useEffect(() => {
    if (loaded) SplashScreen.hideAsync().catch(() => {});
  }, [loaded]);
  if (!loaded) return null;
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: C.bg },
        headerShadowVisible: false,
        headerTintColor: C.text,
        headerTitleStyle: { fontFamily: lang === "en" ? "Inter_600SemiBold" : "Mukta_600SemiBold", fontSize: 18 },
        contentStyle: { backgroundColor: C.bg },
        headerBackButtonDisplayMode: "minimal",
      }}
    >
      <Stack.Protected guard={!token}>
        <Stack.Screen name="welcome" options={{ headerShown: false }} />
      </Stack.Protected>
      <Stack.Protected guard={!!token}>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="lot/[id]" options={{ title: "" }} />
        <Stack.Screen name="make-offer/[id]" options={{ title: t("make_offer") }} />
        <Stack.Screen name="offer/[id]" options={{ title: "" }} />
        <Stack.Screen name="profile-edit" options={{ title: t("edit_profile") }} />
      </Stack.Protected>
    </Stack>
  );
}

export default function Layout() {
  return (
    <SafeAreaProvider>
      <SessionProvider>
        <StatusBar style="dark" />
        <Root />
      </SessionProvider>
    </SafeAreaProvider>
  );
}
