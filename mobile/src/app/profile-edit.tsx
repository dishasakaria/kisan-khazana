// Edit profile and location (PATCH /api/buyers/me).
import { router } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView } from "react-native";

import { BuyerForm } from "@/components/BuyerForm";
import { Notice } from "@/components/ui";
import { api } from "@/lib/api";
import { useSession } from "@/lib/session";
import { S } from "@/lib/theme";

export default function ProfileEdit() {
  const { t, me, setMe } = useSession();
  const [saved, setSaved] = useState(false);
  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={{ padding: S.lg, gap: S.md, paddingBottom: S.xxl }} keyboardShouldPersistTaps="handled">
        {saved ? <Notice kind="success" text={t("saved")} /> : null}
        <BuyerForm
          init={{
            name: me?.name,
            company: me?.company,
            type: me?.type,
            phone: me?.phone,
            locText: me?.location_text,
            loc: me?.lat != null && me.lon != null ? { lat: me.lat, lon: me.lon, src: "saved", district: me.place?.district ?? "" } : null,
          }}
          submitLabel={t("save")}
          onSubmit={async (b) => {
            setMe(await api.updateMe(b));
            setSaved(true);
            router.back();
          }}
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
