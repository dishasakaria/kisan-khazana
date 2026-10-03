// Home: open FPO lots — search, filter sheet, sort; all filtering happens on the server. Pull to refresh, paged.
import { router, useFocusEffect } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { FlatList, Pressable, RefreshControl, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { LotCard, LotSkeleton } from "@/components/LotCard";
import { Button, Chip, Field, Icon, Row, Sheet, StateView, Txt } from "@/components/ui";
import { api, type Lot, type LotQuery, type Sort } from "@/lib/api";
import { errText } from "@/lib/format";
import { useSession } from "@/lib/session";
import { C, R, S, TOUCH } from "@/lib/theme";

const RADII = [10, 25, 50, 100];
const SORTS: Sort[] = ["nearest", "newest", "price_asc", "price_desc", "qty_desc"];
const PAGE = 20;
type Filters = { crop?: string; radius_km?: number; min_price?: number; max_price?: number; min_qty?: number };
const numOrUndef = (s: string) => (s.trim() && isFinite(Number(s)) && Number(s) > 0 ? Number(s) : undefined);

export default function Home() {
  const { t, me, crop, district, lang } = useSession();
  const [q, setQ] = useState("");
  const [qDebounced, setQDebounced] = useState("");
  const [sort, setSort] = useState<Sort>("nearest");
  const [f, setF] = useState<Filters>({});
  const [crops, setCrops] = useState<{ crop: string; lots: number }[]>([]);
  const [items, setItems] = useState<Lot[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [pending, setPending] = useState<Set<number>>(new Set());
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [moreBusy, setMoreBusy] = useState(false);
  const [sheet, setSheet] = useState<"filters" | "sort" | null>(null);
  const reqId = useRef(0);

  useEffect(() => {
    const id = setTimeout(() => setQDebounced(q.trim()), 400);
    return () => clearTimeout(id);
  }, [q]);

  const query = useCallback((p: number): LotQuery => ({ ...f, q: qDebounced || undefined, sort, page: p, limit: PAGE }), [f, qDebounced, sort]);

  const load = useCallback(
    async (mode: "first" | "refresh") => {
      const id = ++reqId.current;
      if (mode === "first") setState("loading");
      else setRefreshing(true);
      try {
        const r = await api.lots(query(1));
        if (id !== reqId.current) return; // a newer search/filter won
        setItems(r.items);
        setTotal(r.total);
        setCrops(r.crops);
        setPage(1);
        setHasMore(r.has_more);
        setState("ready");
      } catch (e) {
        if (id !== reqId.current) return;
        setError(errText(t, e));
        setState("error");
      } finally {
        if (id === reqId.current) setRefreshing(false);
      }
    },
    [query, t],
  );

  useEffect(() => {
    load("first");
  }, [load]);

  useFocusEffect(
    useCallback(() => {
      api.offers().then((os) => setPending(new Set(os.filter((o) => o.status === "sent").map((o) => o.lot_id))), () => {});
    }, []),
  );

  async function loadMore() {
    if (!hasMore || moreBusy || state !== "ready") return;
    setMoreBusy(true);
    const id = reqId.current;
    try {
      const r = await api.lots(query(page + 1));
      if (id !== reqId.current) return;
      setItems((prev) => [...prev, ...r.items.filter((x) => !prev.some((p) => p.id === x.id))]);
      setPage(page + 1);
      setHasMore(r.has_more);
    } catch {
      // keep what we have; the next scroll retries
    } finally {
      setMoreBusy(false);
    }
  }

  const nFilters = Object.values(f).filter((v) => v !== undefined).length;
  const where = me?.place?.town?.[lang] ?? (me?.place?.district ? district(me.place.district) : null);

  const header = (
    <View style={{ gap: S.md, paddingBottom: S.sm }}>
      <Row style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <View style={{ flex: 1 }}>
          <Txt v="title" accessibilityRole="header">
            {t("home_title")}
          </Txt>
          <Pressable onPress={() => router.push("/profile-edit")} accessibilityRole="button" accessibilityLabel={t("change_location")} style={{ minHeight: TOUCH, justifyContent: "center" }}>
            <Row style={{ gap: 4 }}>
              <Icon name="location-outline" size={15} color={C.primary} />
              <Txt v="small" color={C.primary}>
                {where ? t("near_place", { p: me?.location_text || where }) : t("change_location")}
              </Txt>
              <Icon name="chevron-down" size={14} color={C.primary} />
            </Row>
          </Pressable>
        </View>
      </Row>
      <Row style={{ backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: R.md, paddingHorizontal: S.md, minHeight: 48 }}>
        <Icon name="search" size={18} color={C.muted} />
        <TextInput
          value={q}
          onChangeText={setQ}
          placeholder={t("search")}
          placeholderTextColor={C.faint}
          accessibilityLabel={t("search")}
          returnKeyType="search"
          style={{ flex: 1, fontSize: 16, color: C.text, fontFamily: lang === "en" ? "Inter_400Regular" : "Mukta_400Regular", paddingVertical: 10 }}
        />
        {q ? (
          <Pressable onPress={() => setQ("")} hitSlop={10} accessibilityRole="button" accessibilityLabel={t("reset")}>
            <Icon name="close-circle" size={18} color={C.faint} />
          </Pressable>
        ) : null}
      </Row>
      <Row>
        <Button label={nFilters ? `${t("filters")} · ${nFilters}` : t("filters")} icon="options-outline" kind="secondary" onPress={() => setSheet("filters")} style={{ flex: 1, minHeight: TOUCH }} />
        <Button label={t(`sort_${sort}`)} icon="swap-vertical" kind="secondary" onPress={() => setSheet("sort")} style={{ flex: 1, minHeight: TOUCH }} a11yHint={t("sort")} />
      </Row>
      {state === "ready" ? (
        <Txt v="caption" color={C.muted} accessibilityLiveRegion="polite">
          {t("results_n", { n: total })}
        </Txt>
      ) : null}
    </View>
  );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.bg }} edges={["top"]}>
      <FlatList
        data={state === "ready" ? items : []}
        keyExtractor={(l) => String(l.id)}
        contentContainerStyle={{ padding: S.lg, gap: S.md, flexGrow: 1 }}
        ListHeaderComponent={header}
        keyboardShouldPersistTaps="handled"
        renderItem={({ item }) => <LotCard l={item} pending={pending.has(item.id)} onPress={() => router.push(`/lot/${item.id}`)} />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load("refresh")} colors={[C.primary]} />}
        onEndReached={loadMore}
        onEndReachedThreshold={0.4}
        ListEmptyComponent={
          state === "loading" ? (
            <View style={{ gap: S.md }}>
              <LotSkeleton />
              <LotSkeleton />
              <LotSkeleton />
            </View>
          ) : state === "error" ? (
            <StateView icon="cloud-offline-outline" title={t("err_load")} body={error} action={t("retry")} onAction={() => load("first")} />
          ) : (
            <StateView
              icon="cube-outline"
              title={t("none_found")}
              body={t("none_hint")}
              action={nFilters || qDebounced ? t("reset") : t("retry")}
              onAction={() => (nFilters || qDebounced ? (setF({}), setQ("")) : load("first"))}
            />
          )
        }
        ListFooterComponent={moreBusy ? <LotSkeleton /> : null}
      />
      {sheet === "filters" ? <FilterSheet init={f} crops={crops} onClose={() => setSheet(null)} onApply={(nf) => { setF(nf); setSheet(null); }} /> : null}
      <Sheet visible={sheet === "sort"} title={t("sort")} onClose={() => setSheet(null)}>
        <View style={{ gap: S.sm }} accessibilityRole="radiogroup">
          {SORTS.map((s) => (
            <Pressable
              key={s}
              onPress={() => { setSort(s); setSheet(null); }}
              accessibilityRole="radio"
              accessibilityState={{ checked: sort === s }}
              style={{ minHeight: 52, flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: S.md, borderRadius: R.md, backgroundColor: sort === s ? C.primarySoft : C.surface, borderWidth: 1, borderColor: sort === s ? C.primarySoft : C.border }}
            >
              <Txt v="body" color={sort === s ? C.primary : C.text}>
                {t(`sort_${s}`)}
              </Txt>
              {sort === s ? <Icon name="checkmark" color={C.primary} /> : null}
            </Pressable>
          ))}
        </View>
      </Sheet>
    </SafeAreaView>
  );
}

function FilterSheet({ init, crops, onClose, onApply }: { init: Filters; crops: { crop: string; lots: number }[]; onClose: () => void; onApply: (f: Filters) => void }) {
  const { t, crop } = useSession();
  const [cropSel, setCropSel] = useState(init.crop);
  const [radius, setRadius] = useState(init.radius_km);
  const [minP, setMinP] = useState(init.min_price ? String(init.min_price) : "");
  const [maxP, setMaxP] = useState(init.max_price ? String(init.max_price) : "");
  const [minQ, setMinQ] = useState(init.min_qty ? String(init.min_qty) : "");
  const list = cropSel && !crops.some((c) => c.crop === cropSel) ? [...crops, { crop: cropSel, lots: 0 }] : crops;
  return (
    <Sheet
      visible
      title={t("filters")}
      onClose={onClose}
      footer={
        <Row>
          <Button label={t("reset")} kind="secondary" onPress={() => onApply({})} style={{ flex: 1 }} />
          <Button
            label={t("apply")}
            icon="checkmark"
            style={{ flex: 2 }}
            onPress={() => onApply({ crop: cropSel, radius_km: radius, min_price: numOrUndef(minP), max_price: numOrUndef(maxP), min_qty: numOrUndef(minQ) })}
          />
        </Row>
      }
    >
      <View style={{ gap: S.sm }}>
        <Txt v="label">{t("crop")}</Txt>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: S.sm }}>
          <Chip label={t("all_crops")} selected={!cropSel} onPress={() => setCropSel(undefined)} />
          {list.map((c) => (
            <Chip key={c.crop} label={`${crop(c.crop)} · ${c.lots}`} selected={cropSel === c.crop} onPress={() => setCropSel(c.crop)} />
          ))}
        </View>
      </View>
      <View style={{ gap: S.sm }}>
        <Txt v="label">{t("within")}</Txt>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: S.sm }}>
          <Chip label={t("any_km")} selected={radius === undefined} onPress={() => setRadius(undefined)} />
          {RADII.map((r) => (
            <Chip key={r} label={t("km_away", { n: r })} selected={radius === r} onPress={() => setRadius(r)} />
          ))}
        </View>
      </View>
      <View style={{ gap: S.sm }}>
        <Txt v="label">{t("price_range")}</Txt>
        <Row style={{ alignItems: "flex-start" }}>
          <View style={{ flex: 1 }}>
            <Field label={t("min")} value={minP} onChangeText={(s) => setMinP(s.replace(/\D/g, ""))} keyboardType="number-pad" maxLength={6} />
          </View>
          <View style={{ flex: 1 }}>
            <Field label={t("max")} value={maxP} onChangeText={(s) => setMaxP(s.replace(/\D/g, ""))} keyboardType="number-pad" maxLength={6} />
          </View>
        </Row>
      </View>
      <Field label={t("min_qty")} value={minQ} onChangeText={(s) => setMinQ(s.replace(/[^\d.]/g, ""))} keyboardType="decimal-pad" maxLength={7} />
    </Sheet>
  );
}
