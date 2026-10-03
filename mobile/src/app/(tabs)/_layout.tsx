import { Tabs } from "expo-router";
import type { ColorValue } from "react-native";

import { Icon, type IconName } from "@/components/ui";
import { useSession } from "@/lib/session";
import { C } from "@/lib/theme";

const icon = (on: IconName, off: IconName) => ({ focused, color }: { focused: boolean; color: ColorValue }) => (
  <Icon name={focused ? on : off} color={String(color)} size={22} />
);

export default function TabsLayout() {
  const { t, lang } = useSession();
  const font = lang === "en" ? "Inter_600SemiBold" : "Mukta_600SemiBold";
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: C.bg },
        tabBarActiveTintColor: C.primary,
        tabBarInactiveTintColor: C.muted,
        tabBarStyle: { backgroundColor: C.surface, borderTopColor: C.border, minHeight: 60 },
        tabBarLabelStyle: { fontFamily: font, fontSize: 12 },
      }}
    >
      <Tabs.Screen name="index" options={{ title: t("tab_home"), tabBarIcon: icon("home", "home-outline") }} />
      <Tabs.Screen name="offers" options={{ title: t("tab_offers"), tabBarIcon: icon("receipt", "receipt-outline") }} />
      <Tabs.Screen name="profile" options={{ title: t("tab_profile"), tabBarIcon: icon("person-circle", "person-circle-outline") }} />
    </Tabs>
  );
}
