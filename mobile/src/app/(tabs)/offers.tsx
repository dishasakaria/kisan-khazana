// My offers: Pending / Accepted / Rejected. Refreshes on focus and every 20 s while visible.
import { router } from "expo-router";
import { useState } from "react";
import { FlatList, Pressable, RefreshControl, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Icon, Row, Skeleton, StateView, StatusPill, Txt, st } from "@/components/ui";
import { api, type Offer, type OfferStatus } from "@/lib/api";
import { ago, errText, qtl, rs } from "@/lib/format";
import { useSession } from "@/lib/session";
import { C, R, S, TOUCH } from "@/lib/theme";
import { usePoll } from "@/lib/usePoll";

type Tab = OfferStatus | "all";
const TABS: Tab[] = ["all", "sent", "accepted", "rejected"];
const TAB_KEY = { all: "tab_all", sent: "tab_pending", accepted: "tab_accepted", rejected: "tab_rejected" } as const;
const EMPTY_KEY = { all: "none_all", sent: "none_sent", accepted: "none_accepted", rejected: "none_rejected" } as const;

export default function Offers() {
  const { t, crop } = useSession();
  const [tab, setTab] = useState<Tab>("all");
  const [offers, setOffers] = useState<Offer[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  async function load() {
    try {
      setOffers(await api.offers());
      setError(null);
    } catch (e) {
      setError(errText(t, e));
    }
  }
  usePoll(load, 20000);

  const rows = (offers ?? []).filter((o) => tab === "all" || o.status === tab);
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.bg }} edges={["top"]}>
      <View style={{ paddingHorizontal: S.lg, paddingTop: S.lg, gap: S.md }}>
        <Txt v="title" accessibilityRole="header">
          {t("tab_offers")}
        </Txt>
        <View style={{ flexDirection: "row", backgroundColor: C.sunken, borderRadius: R.md, padding: 3, gap: 3 }} accessibilityRole="tablist">
          {TABS.map((s) => {
            const n = (offers ?? []).filter((o) => s === "all" || o.status === s).length;
            const on = tab === s;
            return (
              <Pressable
                key={s}
                onPress={() => setTab(s)}
                accessibilityRole="tab"
                accessibilityState={{ selected: on }}
                accessibilityLabel={`${t(TAB_KEY[s])}, ${n}`}
                style={{ flex: 1, minHeight: TOUCH, alignItems: "center", justifyContent: "center", borderRadius: R.sm, backgroundColor: on ? C.surface : "transparent", borderWidth: 1, borderColor: on ? C.border : "transparent" }}
              >
                <Txt v="label" color={on ? C.primary : C.muted} numberOfLines={1} adjustsFontSizeToFit>
                  {t(TAB_KEY[s])}
                  {offers ? ` · ${n}` : ""}
                </Txt>
              </Pressable>
            );
          })}
        </View>
      </View>
      <FlatList
        data={rows}
        keyExtractor={(o) => String(o.offer_id)}
        contentContainerStyle={{ padding: S.lg, gap: S.md, flexGrow: 1 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await load(); setRefreshing(false); }} colors={[C.primary]} />}
        renderItem={({ item: o }) => (
          <Pressable
            onPress={() => router.push(`/offer/${o.offer_id}`)}
            accessibilityRole="button"
            accessibilityLabel={`${crop(o.crop)}, ${qtl(o.qty_qtl)} ${t("qtl")}, ${rs(o.price_rs_qtl)}${t("per_qtl")}, ${t(`status_${o.status}`)}`}
            style={({ pressed }) => [st.card, { gap: S.sm }, pressed && { backgroundColor: C.sunken }]}
          >
            <Row style={{ justifyContent: "space-between" }}>
              <View style={{ flex: 1 }}>
                <Txt v="h2">{crop(o.crop)}</Txt>
                {o.lot?.fpo ? (
                  <Txt v="small" color={C.muted} numberOfLines={1}>
                    {o.lot.fpo.name}
                  </Txt>
                ) : null}
              </View>
              <StatusPill status={o.status} />
            </Row>
            <Txt v="body">
              {qtl(o.qty_qtl)} {t("qtl")} × {rs(o.price_rs_qtl)} = <Txt v="label">{rs(o.total_value)}</Txt>
            </Txt>
            <Row style={{ justifyContent: "space-between" }}>
              <Txt v="caption" color={C.muted}>
                {t("offer_n", { n: o.offer_id })} · {t("sent_on")} {ago(t, o.created_at)}
              </Txt>
              {o.status === "accepted" ? (
                <Row style={{ gap: 4 }}>
                  <Icon name="call-outline" size={14} color={C.primary} />
                  <Txt v="caption" w="s" color={C.primary}>
                    {t("fpo")}
                  </Txt>
                </Row>
              ) : null}
            </Row>
          </Pressable>
        )}
        ListEmptyComponent={
          offers === null && !error ? (
            <View style={{ gap: S.md }}>
              <Skeleton h={96} />
              <Skeleton h={96} />
            </View>
          ) : error && offers === null ? (
            <StateView icon="cloud-offline-outline" title={t("err_load")} body={error} action={t("retry")} onAction={load} />
          ) : (
            <StateView icon="receipt-outline" title={t(EMPTY_KEY[tab])} body={t("none_offers_hint")} action={t("browse")} onAction={() => router.navigate("/")} />
          )
        }
      />
    </SafeAreaView>
  );
}
