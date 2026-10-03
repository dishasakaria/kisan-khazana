import { Pressable, View } from "react-native";

import type { Lot } from "@/lib/api";
import { ago, qtl, rs } from "@/lib/format";
import { useSession } from "@/lib/session";
import { C, R, S } from "@/lib/theme";
import { Icon, Row, Skeleton, Txt, st } from "./ui";

export function lotPlace(l: Pick<Lot, "km" | "location" | "district">, t: ReturnType<typeof useSession>["t"], district: (d: string | null) => string) {
  return [l.km != null ? t("km_away", { n: l.km }) : null, l.location, l.district && l.location?.includes(l.district) ? null : district(l.district)]
    .filter(Boolean)
    .join(" · ");
}

export function RefDelta({ ask, ref }: { ask: number; ref: number | null }) {
  const { t } = useSession();
  if (ref == null || Math.round(ask - ref) === 0) return null;
  const d = ask - ref;
  return (
    <Row style={{ gap: 4 }}>
      <Icon name={d < 0 ? "arrow-down" : "arrow-up"} size={14} color={C.muted} />
      <Txt v="caption" color={C.muted}>
        {t(d < 0 ? "below_ref" : "above_ref", { n: rs(Math.abs(d)) })}
      </Txt>
    </Row>
  );
}

export function LotCard({ l, pending, onPress }: { l: Lot; pending: boolean; onPress: () => void }) {
  const { t, crop, district } = useSession();
  const where = lotPlace(l, t, district);
  const qtyText = t("of_total", { a: qtl(l.available_qty_qtl), t: qtl(l.total_qty_qtl) });
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={[crop(l.crop), l.fpo?.name, qtyText, `${t("asking")} ${rs(l.asking_price_rs_qtl)}${t("per_qtl")}`, where,
        pending ? t("offer_pending") : ""].filter(Boolean).join(", ")}
      style={({ pressed }) => [st.card, { gap: S.md }, pressed && { backgroundColor: C.sunken }]}
    >
      <Row style={{ alignItems: "flex-start" }}>
        <View style={{ flex: 1 }}>
          <Txt v="h2">{crop(l.crop)}</Txt>
          <Row style={{ gap: 4 }}>
            <Icon name="business-outline" size={14} color={C.muted} />
            <Txt v="small" color={C.muted} numberOfLines={1} style={{ flex: 1 }}>
              {l.fpo?.name}
            </Txt>
          </Row>
        </View>
        {pending ? (
          <View style={[st.pill, { backgroundColor: C.earthSoft }]}>
            <Icon name="time-outline" size={14} color={C.earth} />
            <Txt v="caption" w="s" color={C.earth}>
              {t("offer_pending")}
            </Txt>
          </View>
        ) : null}
      </Row>
      <Row style={{ justifyContent: "space-between", alignItems: "flex-end" }}>
        <View style={{ flex: 1 }}>
          <Txt v="title">
            {rs(l.asking_price_rs_qtl)}
            <Txt v="small" color={C.muted}>
              {" "}
              {t("per_qtl")}
            </Txt>
          </Txt>
          <RefDelta ask={l.asking_price_rs_qtl} ref={l.market_reference_price} />
        </View>
        <View style={{ alignItems: "flex-end" }}>
          <Txt v="label">{qtl(l.available_qty_qtl)} {t("qtl")}</Txt>
          {l.quality ? (
            <Txt v="caption" color={C.muted}>
              {t("quality")}: {l.quality}
            </Txt>
          ) : null}
        </View>
      </Row>
      <View style={{ height: 1, backgroundColor: C.border }} />
      <Row style={{ justifyContent: "space-between" }}>
        <Row style={{ gap: 4, flex: 1 }}>
          <Icon name="location-outline" size={15} color={C.muted} />
          <Txt v="small" color={C.muted} numberOfLines={1} style={{ flex: 1 }}>
            {where}
          </Txt>
        </Row>
        <Txt v="caption" color={C.faint}>
          {ago(t, l.updated_at || l.created_at)}
        </Txt>
      </Row>
    </Pressable>
  );
}

export function LotSkeleton() {
  return (
    <View style={[st.card, { gap: S.md }]} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      <Skeleton h={18} w="45%" />
      <Skeleton h={14} w="60%" />
      <Row style={{ justifyContent: "space-between" }}>
        <Skeleton h={28} w="40%" />
        <Skeleton h={18} w={70} style={{ borderRadius: R.sm }} />
      </Row>
      <Skeleton h={14} w="80%" />
    </View>
  );
}
