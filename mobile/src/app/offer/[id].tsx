// One offer. After "send" it opens with ?sent=1 (the server's real response). Accepted -> farmer contact.
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Linking, RefreshControl, ScrollView, View } from "react-native";

import { lotPlace } from "@/components/LotCard";
import { Button, Card, Icon, Notice, Row, Skeleton, StateView, StatusPill, Txt } from "@/components/ui";
import { api, type FpoContact, type Offer } from "@/lib/api";
import { ago, errText, qtl, rs, shortDate } from "@/lib/format";
import { useSession } from "@/lib/session";
import { C, S } from "@/lib/theme";
import { usePoll } from "@/lib/usePoll";

export default function OfferDetail() {
  const { id, sent } = useLocalSearchParams<{ id: string; sent?: string }>();
  const { t, lang, crop, district } = useSession();
  const decidedAt = (o: Offer) => o.accepted_at ?? o.rejected_at;
  const [o, setO] = useState<Offer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  async function load() {
    try {
      setO(await api.offer(Number(id)));
      setError(null);
    } catch (e) {
      setError(errText(t, e));
    }
  }
  usePoll(load, 20000, o?.status !== "accepted" && o?.status !== "rejected"); // stop polling once decided

  if (!o)
    return error ? (
      <StateView icon="cloud-offline-outline" title={t("err_load")} body={error} action={t("retry")} onAction={load} />
    ) : (
      <View style={{ padding: S.lg, gap: S.md }}>
        <Skeleton h={28} w="50%" />
        <Skeleton h={140} />
      </View>
    );

  const l = o.lot;
  return (
    <ScrollView
      contentContainerStyle={{ padding: S.lg, gap: S.md, paddingBottom: S.xxl }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await load(); setRefreshing(false); }} colors={[C.primary]} />}
    >
      <Stack.Screen options={{ title: t("offer_n", { n: o.offer_id }) }} />
      {sent ? (
        <Card style={{ gap: S.sm, backgroundColor: C.primarySoft, borderColor: C.primarySoft }}>
          <Row>
            <Icon name="checkmark-circle" color={C.primary} size={24} />
            <Txt v="h2" color={C.primary} accessibilityRole="header" accessibilityLiveRegion="polite">
              {t("sent_title")}
            </Txt>
          </Row>
          <Txt v="small">{t("sent_body")}</Txt>
        </Card>
      ) : null}
      <Card style={{ gap: S.md }}>
        <Row style={{ justifyContent: "space-between" }}>
          <Txt v="title">{crop(o.crop)}</Txt>
          <StatusPill status={o.status} />
        </Row>
        <KV k={t("qty")} v={`${qtl(o.qty_qtl)} ${t("qtl")}`} />
        <KV k={t("price")} v={`${rs(o.price_rs_qtl)} ${t("per_qtl")}`} />
        <KV k={t("total")} v={rs(o.total_value)} />
        <KV k={t("fee_amt")} v={rs(o.buyer_fee)} />
        <View style={{ height: 1, backgroundColor: C.border }} />
        <KV k={t("you_pay")} v={rs(o.total_value + (o.buyer_fee ?? 0))} strong />
        <Txt v="caption" color={C.muted}>
          {t("sent_on")} {shortDate(lang, o.created_at)} ({ago(t, o.created_at)})
          {decidedAt(o) ? ` · ${t("decided_on")} ${shortDate(lang, decidedAt(o))} (${ago(t, decidedAt(o))})` : ""}
        </Txt>
        {l ? (
          <Row style={{ gap: 4 }}>
            <Icon name="location-outline" size={15} color={C.muted} />
            <Txt v="small" color={C.muted}>
              {t("lot", { n: l.id })}
              {l.fpo ? ` · ${l.fpo.name}` : ""} · {lotPlace(l, t, district)}
            </Txt>
          </Row>
        ) : null}
      </Card>
      {o.status === "accepted" && o.fpo_contact ? (
        <FpoCard c={o.fpo_contact} />
      ) : (
        <Notice kind={o.status === "rejected" ? "error" : "info"} text={t(o.status === "rejected" ? "rejected_note" : "pending_note")} />
      )}
      {o.status === "sent" ? <Notice text={t("contact_after")} /> : null}
      {error ? <Notice kind="error" text={error} /> : null}
      {sent ? <Button label={t("back_home")} kind="secondary" icon="storefront-outline" onPress={() => router.navigate("/")} /> : null}
      <Button label={t("tab_offers")} kind="ghost" icon="receipt-outline" onPress={() => router.navigate("/offers")} />
    </ScrollView>
  );
}

function FpoCard({ c }: { c: FpoContact }) {
  const { t, district } = useSession();
  const [err, setErr] = useState<string | null>(null);
  const open = (url: string) => Linking.openURL(url).catch(() => setErr(t("open_failed")));
  const tel = c.phone?.replace(/[^\d+]/g, "");
  return (
    <Card style={{ gap: S.md, borderColor: C.primary }}>
      <Txt v="caption" color={C.muted}>
        {t("fpo")}
      </Txt>
      <Row>
        <Icon name="business-outline" size={26} color={C.primary} />
        <View style={{ flex: 1 }}>
          <Txt v="h2">{c.name}</Txt>
          {c.phone ? (
            <Txt v="small" color={C.muted} selectable>
              {c.phone}
            </Txt>
          ) : null}
        </View>
      </Row>
      {c.pickup ? <Info icon="cube-outline" k={t("pickup_at")} v={c.pickup} /> : null}
      {c.address && c.address !== c.pickup ? <Info icon="location-outline" k={t("address")} v={[c.address, district(c.district)].filter(Boolean).join(", ")} /> : null}
      <Notice kind="success" text={t("accepted_note")} />
      {tel ? (
        <Row>
          <Button label={t("call")} icon="call-outline" onPress={() => open(`tel:${tel}`)} style={{ flex: 1 }} a11yHint={c.phone ?? undefined} />
          {c.whatsapp ? <Button label={t("whatsapp")} icon="logo-whatsapp" kind="secondary" onPress={() => open(c.whatsapp!)} style={{ flex: 1 }} /> : null}
        </Row>
      ) : null}
      {err ? <Notice kind="error" text={err} /> : null}
    </Card>
  );
}

function Info({ icon, k, v }: { icon: "cube-outline" | "location-outline"; k: string; v: string }) {
  return (
    <Row style={{ alignItems: "flex-start" }}>
      <View style={{ paddingTop: 2 }}>
        <Icon name={icon} size={18} color={C.muted} />
      </View>
      <View style={{ flex: 1 }}>
        <Txt v="caption" color={C.muted}>
          {k}
        </Txt>
        <Txt v="body" selectable>
          {v}
        </Txt>
      </View>
    </Row>
  );
}

function KV({ k, v, strong }: { k: string; v: string; strong?: boolean }) {
  return (
    <Row style={{ justifyContent: "space-between" }}>
      <Txt v={strong ? "label" : "small"} color={strong ? C.text : C.muted}>
        {k}
      </Txt>
      <Txt v={strong ? "h2" : "label"}>{v}</Txt>
    </Row>
  );
}
