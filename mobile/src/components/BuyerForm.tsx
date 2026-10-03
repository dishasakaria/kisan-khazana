// Registration and profile edit share one form. Server validates again; its error codes map to messages.
import { useState } from "react";
import { View } from "react-native";

import { BUYER_TYPES, type BuyerInput, type BuyerType } from "@/lib/api";
import { errText } from "@/lib/format";
import { useSession } from "@/lib/session";
import { C, S } from "@/lib/theme";
import { LocationPicker, type Picked } from "./LocationPicker";
import { Button, Card, Chip, Field, Notice, Txt } from "./ui";

export type FormInit = { name?: string; company?: string | null; type?: BuyerType; phone?: string | null; locText?: string | null; loc?: Picked | null };

export function BuyerForm({ init, withPin, submitLabel, onSubmit }: { init?: FormInit; withPin?: boolean; submitLabel: string; onSubmit: (b: BuyerInput) => Promise<void> }) {
  const { t } = useSession();
  const [name, setName] = useState(init?.name ?? "");
  const [company, setCompany] = useState(init?.company ?? "");
  const [type, setType] = useState<BuyerType>(init?.type ?? "wholesale");
  const [phone, setPhone] = useState((init?.phone ?? "").replace(/\D/g, "").slice(-10));
  const [loc, setLoc] = useState<Picked | null>(init?.loc ?? null);
  const [locText, setLocText] = useState(init?.locText ?? "");
  const [pin, setPin] = useState("");
  const [err, setErr] = useState<{ field?: string; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (name.trim().length < 2) return setErr({ field: "name", text: t("err_bad_name") });
    if (!/^[6-9]\d{9}$/.test(phone)) return setErr({ field: "phone", text: t("err_bad_phone") });
    if (withPin && !/^\d{4,6}$/.test(pin)) return setErr({ field: "pin", text: t("err_bad_pin") });
    if (!loc) return setErr({ field: "loc", text: t("need_loc") });
    setErr(null);
    setBusy(true);
    try {
      await onSubmit({ name: name.trim(), company: company.trim(), type, phone, lat: loc.lat, lon: loc.lon, location_text: locText.trim(),
        ...(withPin ? { pin } : {}) });
    } catch (e) {
      setErr({ text: errText(t, e) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={{ gap: S.lg }}>
      <Card style={{ gap: S.lg }}>
        <Field label={t("name")} value={name} onChangeText={setName} autoComplete="name" maxLength={80} error={err?.field === "name" ? err.text : null} />
        <Field label={`${t("company")} (${t("optional")})`} value={company} onChangeText={setCompany} autoComplete="organization" maxLength={120} />
        <View style={{ gap: S.sm }}>
          <Txt v="label">{t("type")}</Txt>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: S.sm }} accessibilityRole="radiogroup">
            {BUYER_TYPES.map((ty) => (
              <Chip key={ty} label={t(`type_${ty}`)} selected={type === ty} onPress={() => setType(ty)} />
            ))}
          </View>
        </View>
        <Field
          label={t("phone")}
          hint={t("phone_why")}
          value={phone}
          onChangeText={(s) => setPhone(s.replace(/\D/g, "").slice(-10))}
          keyboardType="phone-pad"
          autoComplete="tel"
          placeholder="98XXXXXXXX"
          maxLength={10}
          error={err?.field === "phone" ? err.text : null}
        />
        {withPin ? (
          <Field
            label={t("pin")}
            hint={t("pin_why")}
            value={pin}
            onChangeText={(s) => setPin(s.replace(/\D/g, "").slice(0, 6))}
            keyboardType="number-pad"
            secureTextEntry
            autoComplete="off"
            maxLength={6}
            error={err?.field === "pin" ? err.text : null}
          />
        ) : null}
      </Card>
      <Card style={{ gap: S.sm }}>
        <Txt v="h2">{t("location")}</Txt>
        <LocationPicker value={loc} onChange={setLoc} />
        <Field label={`${t("location_text")} (${t("optional")})`} value={locText} onChangeText={setLocText} maxLength={120} />
        {err?.field === "loc" ? <Notice kind="error" text={err.text} /> : null}
      </Card>
      {err && !err.field ? <Notice kind="error" text={err.text} /> : null}
      <Button label={busy ? t("saving") : submitLabel} onPress={submit} loading={busy} icon="checkmark" />
      <Txt v="caption" color={C.muted} style={{ textAlign: "center" }}>
        {t("fee")}
      </Txt>
    </View>
  );
}
