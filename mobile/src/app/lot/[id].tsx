// One FPO lot: price vs market reference, availability, quality, and the FPO (name + district only until accepted).
import { router, Stack, useLocalSearchParams } from "expo-router";
import { useCallback, useState } from "react";
import { RefreshControl, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { lotPlace, RefDelta } from "@/components/LotCard";
import { Button, Card, Icon, Notice, Row, Skeleton, StateView, Txt, type IconName } from "@/components/ui";
import { api, type Lot } from "@/lib/api";
import { ago, errText, qtl, rs } from "@/lib/format";
import { useSession } from "@/lib/session";
import { C, S } from "@/lib/theme";
import { usePoll } from "@/lib/usePoll";

export default function LotDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { t, crop, district } = useSession();
  const insets = useSafeAreaInsets();
  const [l, setL] = useState<Lot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setL(await api.lot(Number(id)));
      setError(null);
    } catch (e) {
      setError(errText(t, e));
    }
  }, [id, t]);
  usePoll(load, 30000); // availability changes as the FPO accepts other offers

  if (!l)
    return error ? (
      <StateView icon="cloud-offline-outline" title={t("err_load")} body={error} action={t("retry")} onAction={load} />
    ) : (
      <View style={{ padding: S.lg, gap: S.md }}>
        <Skeleton h={30} w="50%" />
        <Skeleton h={130} />
        <Skeleton h={110} />
      </View>
    );

  const pending = l.my_offer?.status === "sent";
  const open = l.status === "open" && l.available_qty_qtl > 0;
  return (
    <View style={{ flex: 1 }}>
      <Stack.Screen options={{ title: t("lot", { n: l.id }) }} />
      <ScrollView
        contentContainerStyle={{ padding: S.lg, gap: S.md, paddingBottom: 140 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await load(); setRefreshing(false); }} colors={[C.primary]} />}
      >
        <View>
          <Txt v="display" accessibilityRole="header">
            {crop(l.crop)}
          </Txt>
          <Txt color={C.muted}>{t("of_total", { a: qtl(l.available_qty_qtl), t: qtl(l.total_qty_qtl) })}</Txt>
        </View>
        <Card style={{ gap: S.md }}>
          <Row style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
            <View>
              <Txt v="caption" color={C.muted}>
                {t("asking")}
              </Txt>
              <Txt v="display">{rs(l.asking_price_rs_qtl)}</Txt>
              <Txt v="small" color={C.muted}>
                {t("per_qtl")}
              </Txt>
            </View>
            {l.market_reference_price ? (
              <View style={{ alignItems: "flex-end" }}>
                <Txt v="caption" color={C.muted}>
                  {t("market_ref")}
                </Txt>
                <Txt v="h2">{rs(l.market_reference_price)}</Txt>
              </View>
            ) : null}
          </Row>
          <RefDelta ask={l.asking_price_rs_qtl} ref={l.market_reference_price} />
        </Card>
        <Card style={{ gap: S.md }}>
          <Fact icon="location-outline" k={t("where")} v={lotPlace(l, t, district)} />
          {l.quality ? <Fact icon="ribbon-outline" k={t("quality")} v={l.quality} /> : null}
          {l.notes ? <Fact icon="document-text-outline" k={t("notes")} v={l.notes} /> : null}
          <Fact icon="time-outline" k="" v={t("updated_ago", { t: ago(t, l.updated_at || l.created_at) })} />
          <Fact icon="car-outline" k="" v={t("pickup")} />
        </Card>
        {l.fpo ? (
          <Card style={{ gap: S.sm }}>
            <Txt v="caption" color={C.muted}>
              {t("about_fpo")}
            </Txt>
            <Row>
              <Icon name="business-outline" size={24} color={C.primary} />
              <View style={{ flex: 1 }}>
                <Txt v="h2">{l.fpo.name}</Txt>
                {l.fpo.district ? <Txt v="small" color={C.muted}>{t("district_of", { d: district(l.fpo.district) })}</Txt> : null}
              </View>
            </Row>
            {l.farmers_n ? <Txt v="small">{t("farmers_n", { n: l.farmers_n })}</Txt> : null}
            <Txt v="small" color={C.muted}>
              {t("fpo_what")}
            </Txt>
          </Card>
        ) : null}
        <Notice text={t("contact_after")} />
        <Notice text={t("fee")} />
      </ScrollView>
      <View style={{ position: "absolute", left: 0, right: 0, bottom: 0, padding: S.lg, paddingBottom: S.lg + insets.bottom, backgroundColor: C.bg, borderTopWidth: 1, borderTopColor: C.border, gap: S.sm }}>
        {pending ? (
          <>
            <Notice text={t("already_offered")} />
            <Button label={t("view_offer")} kind="secondary" icon="receipt-outline" onPress={() => router.push(`/offer/${l.my_offer!.id}`)} />
          </>
        ) : open ? (
          <Button label={t("offer")} icon="pricetag-outline" onPress={() => router.push(`/make-offer/${l.id}`)} />
        ) : (
          <Notice kind="error" text={t("lot_closed")} />
        )}
      </View>
    </View>
  );
}

function Fact({ icon, k, v }: { icon: IconName; k: string; v: string }) {
  return (
    <Row style={{ alignItems: "flex-start" }}>
      <View style={{ paddingTop: 2 }}>
        <Icon name={icon} size={18} color={C.muted} />
      </View>
      <View style={{ flex: 1 }}>
        {k ? (
          <Txt v="caption" color={C.muted}>
            {k}
          </Txt>
        ) : null}
        <Txt v="body">{v}</Txt>
      </View>
    </Row>
  );
}
