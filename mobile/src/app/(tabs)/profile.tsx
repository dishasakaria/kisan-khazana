// Profile: details, edit/location, language, about + how it works, support, logout, version.
import Constants from "expo-constants";
import { router } from "expo-router";
import { Alert, Linking, ScrollView, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button, Card, Icon, LangSwitch, Row, Txt, type IconName } from "@/components/ui";
import { API_BASE } from "@/lib/api";
import { useSession } from "@/lib/session";
import { C, S } from "@/lib/theme";

// optional build-time contacts; the buttons only appear when they are set
const SUPPORT_EMAIL = process.env.EXPO_PUBLIC_SUPPORT_EMAIL ?? "";
const SUPPORT_PHONE = process.env.EXPO_PUBLIC_SUPPORT_PHONE ?? "";

export default function Profile() {
  const { t, me, district, lang, signOut } = useSession();
  const where = me?.place?.town?.[lang] ?? district(me?.place?.district);
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.bg }} edges={["top"]}>
      <ScrollView contentContainerStyle={{ padding: S.lg, gap: S.md, paddingBottom: S.xxl }}>
        <Txt v="title" accessibilityRole="header">
          {t("tab_profile")}
        </Txt>
        <Card style={{ gap: S.md }}>
          <Row>
            <Icon name="business-outline" size={26} color={C.primary} />
            <View style={{ flex: 1 }}>
              <Txt v="h2">{me?.company || me?.name || "—"}</Txt>
              {me?.company ? <Txt v="small" color={C.muted}>{me.name}</Txt> : null}
            </View>
          </Row>
          <Info icon="pricetags-outline" text={me ? t(`type_${me.type}`) : "—"} />
          <Info icon="call-outline" text={me?.phone ?? "—"} />
          <Info icon="location-outline" text={[me?.location_text, where].filter(Boolean).join(" · ") || "—"} />
          <Row>
            <Button label={t("edit_profile")} kind="secondary" icon="create-outline" onPress={() => router.push("/profile-edit")} style={{ flex: 1 }} />
          </Row>
        </Card>
        <Card style={{ gap: S.md }}>
          <Txt v="h2">{t("language")}</Txt>
          <LangSwitch />
        </Card>
        <Card style={{ gap: S.md }}>
          <Txt v="h2">{t("about")}</Txt>
          <Txt v="small">{t("about_body")}</Txt>
          <Txt v="label" style={{ marginTop: S.xs }}>
            {t("how_title")}
          </Txt>
          {(["how1", "how2", "how3", "how4"] as const).map((k, i) => (
            <Row key={k} style={{ alignItems: "flex-start" }}>
              <View style={{ width: 26, height: 26, borderRadius: 13, backgroundColor: C.primarySoft, alignItems: "center", justifyContent: "center" }}>
                <Txt v="label" color={C.primary}>
                  {i + 1}
                </Txt>
              </View>
              <Txt v="small" style={{ flex: 1 }}>
                {t(k)}
              </Txt>
            </Row>
          ))}
          <Txt v="caption" color={C.muted}>
            {t("fee")}
          </Txt>
        </Card>
        <Card style={{ gap: S.md }}>
          <Txt v="h2">{t("support")}</Txt>
          <Txt v="small">{t("support_body")}</Txt>
          {SUPPORT_EMAIL || SUPPORT_PHONE ? (
            <Row>
              {SUPPORT_EMAIL ? <Button label={t("email_us")} kind="secondary" icon="mail-outline" onPress={() => Linking.openURL(`mailto:${SUPPORT_EMAIL}`).catch(() => {})} style={{ flex: 1 }} /> : null}
              {SUPPORT_PHONE ? <Button label={t("call_us")} kind="secondary" icon="call-outline" onPress={() => Linking.openURL(`tel:${SUPPORT_PHONE}`).catch(() => {})} style={{ flex: 1 }} /> : null}
            </Row>
          ) : null}
        </Card>
        <Button
          label={t("logout")}
          kind="ghost"
          icon="log-out-outline"
          onPress={() =>
            Alert.alert(t("logout"), t("logout_q"), [
              { text: t("cancel"), style: "cancel" },
              { text: t("logout"), style: "destructive", onPress: () => signOut() },
            ])
          }
        />
        <Txt v="caption" color={C.faint} style={{ textAlign: "center" }}>
          {t("app_name")} · {t("version", { v: Constants.expoConfig?.version ?? "1.0.0" })} · {t("server")}: {API_BASE.replace(/^https?:\/\//, "")}
        </Txt>
      </ScrollView>
    </SafeAreaView>
  );
}

function Info({ icon, text }: { icon: IconName; text: string }) {
  return (
    <Row>
      <Icon name={icon} size={18} color={C.muted} />
      <Txt v="body" style={{ flex: 1 }}>
        {text}
      </Txt>
    </Row>
  );
}
