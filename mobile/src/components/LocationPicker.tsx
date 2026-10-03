// Location: GPS (asked only when tapped) or manual fallback: 6-digit pincode / district list (bundled, offline).
import * as Location from "expo-location";
import { useState } from "react";
import { View } from "react-native";

import districts from "@/geo/districts.json";
import pincodes from "@/geo/pincodes.json";
import { useSession } from "@/lib/session";
import { C, S } from "@/lib/theme";
import { Button, Chip, Field, Icon, Notice, Row, Txt } from "./ui";

export type Picked = { lat: number; lon: number; src: "gps" | "pin" | "district" | "saved"; pin?: string; district: string };

const PINS = pincodes as Record<string, number[]>;
const DISTRICTS = districts as { name: string; lat: number; lon: number }[];

export function nearestDistrict(lat: number, lon: number): string {
  const k = Math.cos((lat * Math.PI) / 180) ** 2;
  let best = DISTRICTS[0]!;
  for (const d of DISTRICTS) {
    if ((d.lat - lat) ** 2 + k * (d.lon - lon) ** 2 < (best.lat - lat) ** 2 + k * (best.lon - lon) ** 2) best = d;
  }
  return best.name;
}

export function LocationPicker({ value, onChange }: { value: Picked | null; onChange: (p: Picked) => void }) {
  const { t, district } = useSession();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [pin, setPin] = useState("");
  const [showList, setShowList] = useState(false);

  async function gps() {
    setMsg(null);
    setBusy(true);
    try {
      const perm = await Location.requestForegroundPermissionsAsync();
      if (perm.status !== "granted") return setMsg(t("gps_denied"));
      const pos =
        (await Promise.race([
          Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }),
          new Promise<null>((r) => setTimeout(() => r(null), 15000)),
        ])) ?? (await Location.getLastKnownPositionAsync());
      if (!pos) return setMsg(t("gps_fail"));
      const { latitude: lat, longitude: lon } = pos.coords;
      onChange({ lat, lon, src: "gps", district: nearestDistrict(lat, lon) });
    } catch {
      setMsg(t("gps_fail"));
    } finally {
      setBusy(false);
    }
  }

  function usePin() {
    const [lat, lon] = PINS[pin] ?? [];
    if (!/^\d{6}$/.test(pin) || lat == null || lon == null) return setMsg(t("bad_pin"));
    setMsg(null);
    onChange({ lat, lon, src: "pin", pin, district: nearestDistrict(lat, lon) });
  }

  const label = value
    ? value.src === "pin"
      ? `${t("pin_label", { p: value.pin ?? "" })} · ${district(value.district)}`
      : value.src === "gps"
        ? `${t("gps_label")} · ${district(value.district)}`
        : district(value.district)
    : null;

  return (
    <View style={{ gap: S.md }}>
      <Txt v="small" color={C.muted}>
        {t("loc_why")}
      </Txt>
      {label ? (
        <Row style={{ backgroundColor: C.primarySoft, padding: S.md, borderRadius: 10 }}>
          <Icon name="location" color={C.primary} size={18} />
          <Txt v="label" color={C.primary} style={{ flex: 1 }} accessibilityLiveRegion="polite">
            {t("loc_set", { p: label })}
          </Txt>
        </Row>
      ) : null}
      <Button label={busy ? t("locating") : t("use_gps")} icon="navigate-outline" kind="secondary" loading={busy} onPress={gps} />
      <Row style={{ alignItems: "flex-end" }}>
        <View style={{ flex: 1 }}>
          <Field
            label={t("or_pin")}
            value={pin}
            onChangeText={(s) => setPin(s.replace(/\D/g, "").slice(0, 6))}
            keyboardType="number-pad"
            maxLength={6}
            placeholder="422001"
            returnKeyType="done"
            onSubmitEditing={usePin}
          />
        </View>
        <Button label={t("use_pin")} kind="secondary" onPress={usePin} disabled={pin.length !== 6} />
      </Row>
      {msg ? <Notice kind="error" text={msg} /> : null}
      <Button
        label={t("or_district")}
        kind="ghost"
        icon={showList ? "chevron-up" : "chevron-down"}
        onPress={() => setShowList((s) => !s)}
        style={{ alignSelf: "flex-start", paddingHorizontal: S.sm }}
      />
      {showList ? (
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: S.sm }}>
          {DISTRICTS.map((d) => (
            <Chip
              key={d.name}
              label={district(d.name)}
              selected={value?.src === "district" && value.district === d.name}
              onPress={() => {
                setMsg(null);
                onChange({ lat: d.lat, lon: d.lon, src: "district", district: d.name });
              }}
            />
          ))}
        </View>
      ) : null}
    </View>
  );
}
