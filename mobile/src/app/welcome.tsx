// First run: language, then Create account or Log in (mobile number + PIN restores the account on a new phone).
import { useState } from "react";
import { Image, KeyboardAvoidingView, Platform, ScrollView, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { BuyerForm } from "@/components/BuyerForm";
import { Button, Card, Field, LangSwitch, Notice, Row, Txt } from "@/components/ui";
import { api } from "@/lib/api";
import { errText } from "@/lib/format";
import { useSession } from "@/lib/session";
import { C, S } from "@/lib/theme";

export default function Welcome() {
  const { t, signIn } = useSession();
  const [step, setStep] = useState<"start" | "register" | "login">("start");
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.bg }} edges={["top", "bottom"]}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ScrollView contentContainerStyle={{ padding: S.xl, gap: S.xl }} keyboardShouldPersistTaps="handled">
          <Row style={{ gap: S.md, marginTop: S.md }}>
            <Image source={require("../../assets/splash-icon.png")} style={{ width: 44, height: 44 }} accessible={false} />
            <Txt v="title">{t("app_name")}</Txt>
          </Row>
          {step === "start" ? (
            <>
              <View style={{ gap: S.sm }}>
                <Txt v="display" accessibilityRole="header">
                  {t("tagline")}
                </Txt>
                <Txt color={C.muted}>{t("buy_sub")}</Txt>
              </View>
              <Card style={{ gap: S.lg }}>
                <Txt v="h2">{t("choose_lang")} · भाषा · Language</Txt>
                <LangSwitch />
              </Card>
              <View style={{ gap: S.md }}>
                <Button label={t("create_account")} icon="person-add-outline" onPress={() => setStep("register")} />
                <Button label={t("have_account")} kind="secondary" icon="log-in-outline" onPress={() => setStep("login")} />
              </View>
              <Txt v="caption" color={C.muted} style={{ textAlign: "center" }}>
                {t("fee")}
              </Txt>
            </>
          ) : (
            <View style={{ gap: S.lg }}>
              <Row style={{ justifyContent: "space-between" }}>
                <Txt v="title" accessibilityRole="header">
                  {t(step === "register" ? "reg_title" : "login_title")}
                </Txt>
                <Button label={t("back")} kind="ghost" icon="arrow-back" onPress={() => setStep("start")} />
              </Row>
              {step === "register" ? (
                <BuyerForm
                  withPin
                  submitLabel={t("register")}
                  onSubmit={async (b) => {
                    const r = await api.register(b);
                    await signIn(r.buyer_token, r.buyer); // guard flips to the tabs
                  }}
                />
              ) : (
                <Login onDone={signIn} />
              )}
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Login({ onDone }: { onDone: ReturnType<typeof useSession>["signIn"] }) {
  const { t } = useSession();
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!/^[6-9]\d{9}$/.test(phone)) return setErr(t("err_bad_phone"));
    if (!/^\d{4,6}$/.test(pin)) return setErr(t("err_bad_pin"));
    setErr(null);
    setBusy(true);
    try {
      const r = await api.login(phone, pin);
      await onDone(r.buyer_token, r.buyer);
    } catch (e) {
      setErr(errText(t, e));
      setBusy(false);
    }
  }

  return (
    <Card style={{ gap: S.lg }}>
      <Txt v="small" color={C.muted}>
        {t("login_hint")}
      </Txt>
      <Field label={t("phone")} value={phone} onChangeText={(s) => setPhone(s.replace(/\D/g, "").slice(-10))} keyboardType="phone-pad" autoComplete="tel" placeholder="98XXXXXXXX" maxLength={10} />
      <Field label={t("pin")} value={pin} onChangeText={(s) => setPin(s.replace(/\D/g, "").slice(0, 6))} keyboardType="number-pad" secureTextEntry maxLength={6} onSubmitEditing={submit} />
      {err ? <Notice kind="error" text={err} /> : null}
      <Button label={t("login")} icon="log-in-outline" onPress={submit} loading={busy} />
    </Card>
  );
}
