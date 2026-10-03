// Make an offer: quantity + ₹/quintal with a live total and 1% fee preview. The server validates and recalculates.
import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Button, Card, Field, Notice, Row, Skeleton, StateView, Txt } from "@/components/ui";
import { api, type Lot } from "@/lib/api";
import { errText, qtl, rs } from "@/lib/format";
import { useSession } from "@/lib/session";
import { C, R, S } from "@/lib/theme";

const FEE = 0.01;
const num = (s: string) => (s.trim() === "" ? NaN : Number(s.replace(",", ".")));

export default function MakeOffer() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { t, crop } = useSession();
  const insets = useSafeAreaInsets();
  const [l, setL] = useState<Lot | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [p, setP] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const lot = await api.lot(Number(id));
      setL(lot);
      setQ((v) => v || String(lot.available_qty_qtl));
      setP((v) => v || String(Math.round(lot.asking_price_rs_qtl)));
      setLoadErr(null);
    } catch (e) {
      setLoadErr(errText(t, e));
    }
  }
  useEffect(() => {
    load();
  }, [id]);

  if (!l) return loadErr ? <StateView icon="cloud-offline-outline" title={t("err_load")} body={loadErr} action={t("retry")} onAction={load} /> : <View style={{ padding: S.lg, gap: S.md }}><Skeleton h={30} w="60%" /><Skeleton h={160} /></View>;

  const qty = num(q);
  const price = num(p);
  const qtyOk = isFinite(qty) && qty > 0 && qty <= l.available_qty_qtl;
  const priceOk = isFinite(price) && price > 0 && price <= 100000;
  const value = qtyOk && priceOk ? qty * price : null;
  const fee = value != null ? Math.round(value * FEE) : null;

  async function send() {
    if (!l) return;
    if (!qtyOk) return setErr(t("err_bad_qty"));
    if (!priceOk) return setErr(t("err_bad_price"));
    setErr(null);
    setBusy(true);
    try {
      const r = await api.makeOffer(l.id, qty, price);
      router.replace(`/offer/${r.offer_id}?sent=1`); // success screen shows the server's own record
    } catch (e) {
      setErr(errText(t, e));
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={{ padding: S.lg, gap: S.lg, paddingBottom: S.xxl + insets.bottom }} keyboardShouldPersistTaps="handled">
        <View>
          <Txt v="title" accessibilityRole="header">
            {crop(l.crop)} · {l.fpo?.name}
          </Txt>
          <Txt v="small" color={C.muted}>
            {t("of_total", { a: qtl(l.available_qty_qtl), t: qtl(l.total_qty_qtl) })} · {t("asking")} {rs(l.asking_price_rs_qtl)}
            {t("per_qtl")}
          </Txt>
        </View>
        <Card style={{ gap: S.lg }}>
          <Field label={t("qty")} hint={t("max_qty", { n: qtl(l.available_qty_qtl) })} value={q} onChangeText={(s) => setQ(s.replace(/[^\d.,]/g, ""))} keyboardType="decimal-pad" maxLength={8} />
          <Field label={t("your_price")} value={p} onChangeText={(s) => setP(s.replace(/\D/g, ""))} keyboardType="number-pad" maxLength={6} />
        </Card>
        <View style={{ backgroundColor: C.surface, borderRadius: R.md, borderWidth: 1, borderColor: C.border, padding: S.lg, gap: S.sm }} accessibilityLiveRegion="polite">
          <Line k={t("total")} v={rs(value)} />
          <Line k={t("fee_amt")} v={rs(fee)} />
          <View style={{ height: 1, backgroundColor: C.border }} />
          <Line k={t("you_pay")} v={rs(value != null && fee != null ? value + fee : null)} strong />
          <Txt v="caption" color={C.muted}>
            {t("server_checks")}
          </Txt>
        </View>
        <Notice text={t("contact_after")} />
        {err ? <Notice kind="error" text={err} /> : null}
        <Row>
          <Button label={t("cancel")} kind="secondary" onPress={() => router.back()} style={{ flex: 1 }} />
          <Button label={busy ? t("sending") : t("send")} icon="paper-plane-outline" onPress={send} loading={busy} style={{ flex: 2 }} />
        </Row>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function Line({ k, v, strong }: { k: string; v: string; strong?: boolean }) {
  return (
    <Row style={{ justifyContent: "space-between" }}>
      <Txt v={strong ? "label" : "small"} color={strong ? C.text : C.muted}>
        {k}
      </Txt>
      <Txt v={strong ? "h2" : "label"}>{v}</Txt>
    </Row>
  );
}
