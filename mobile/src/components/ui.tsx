// Small design system: text, buttons, chips, cards, skeletons, status pills, form fields, states.
import Ionicons from "@expo/vector-icons/Ionicons";
import { useEffect, useRef, type ComponentProps, type ReactNode } from "react";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import {
  ActivityIndicator,
  Animated,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type StyleProp,
  type TextInputProps,
  type TextStyle,
  type ViewStyle,
} from "react-native";

import type { OfferStatus } from "@/lib/api";
import { LANGS } from "@/lib/i18n";
import { useSession } from "@/lib/session";
import { C, R, S, TOUCH } from "@/lib/theme";

export type IconName = ComponentProps<typeof Ionicons>["name"];
export const Icon = ({ name, size = 20, color = C.text }: { name: IconName; size?: number; color?: string }) => (
  <Ionicons name={name} size={size} color={color} accessible={false} importantForAccessibility="no" />
);

const SIZES = {
  display: [28, 36, "b"],
  title: [22, 30, "b"],
  h2: [18, 26, "s"],
  body: [16, 24, "r"],
  small: [14, 20, "r"],
  label: [14, 20, "s"],
  caption: [12, 17, "r"],
} as const;
type Variant = keyof typeof SIZES;
const FONTS = {
  deva: { r: "Mukta_400Regular", s: "Mukta_600SemiBold", b: "Mukta_700Bold" },
  latin: { r: "Inter_400Regular", s: "Inter_600SemiBold", b: "Inter_700Bold" },
};

export function Txt({
  v = "body",
  w,
  color = C.text,
  style,
  children,
  ...rest
}: {
  v?: Variant;
  w?: "r" | "s" | "b";
  color?: string;
  style?: StyleProp<TextStyle>;
  children: ReactNode;
} & Omit<ComponentProps<typeof Text>, "style">) {
  const { lang } = useSession();
  const [size, lh, weight] = SIZES[v];
  const fam = FONTS[lang === "en" ? "latin" : "deva"][w ?? weight];
  return (
    <Text style={[{ fontFamily: fam, fontSize: size, lineHeight: lh + (lang === "en" ? 0 : 2), color }, style]} {...rest}>
      {children}
    </Text>
  );
}

type BtnKind = "primary" | "secondary" | "ghost";
export function Button({
  label,
  onPress,
  kind = "primary",
  icon,
  loading,
  disabled,
  style,
  a11yHint,
}: {
  label: string;
  onPress: () => void;
  kind?: BtnKind;
  icon?: IconName;
  loading?: boolean;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  a11yHint?: string;
}) {
  const fg = kind === "primary" ? C.white : C.primary;
  const off = disabled || loading;
  return (
    <Pressable
      onPress={onPress}
      disabled={off}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={a11yHint}
      accessibilityState={{ disabled: !!off, busy: !!loading }}
      style={({ pressed }) => [
        st.btn,
        kind === "primary" && { backgroundColor: pressed ? C.primaryPressed : C.primary },
        kind === "secondary" && { backgroundColor: pressed ? C.primarySoft : C.surface, borderColor: C.border, borderWidth: 1 },
        kind === "ghost" && { backgroundColor: pressed ? C.sunken : "transparent" },
        off && { opacity: 0.55 },
        style,
      ]}
    >
      {loading ? <ActivityIndicator color={fg} /> : icon ? <Icon name={icon} color={fg} size={18} /> : null}
      <Txt v="label" color={fg} style={{ fontSize: 15 }}>
        {label}
      </Txt>
    </Pressable>
  );
}

export function Chip({ label, selected, onPress, a11yLabel }: { label: string; selected: boolean; onPress: () => void; a11yLabel?: string }) {
  return (
    <Pressable
      onPress={onPress}
      hitSlop={4}
      accessibilityRole="button"
      accessibilityLabel={a11yLabel ?? label}
      accessibilityState={{ selected }}
      style={[st.chip, selected ? { backgroundColor: C.primary, borderColor: C.primary } : null]}
    >
      {selected ? <Icon name="checkmark" size={14} color={C.white} /> : null}
      <Txt v="label" color={selected ? C.white : C.text}>
        {label}
      </Txt>
    </Pressable>
  );
}

export const Card = ({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) => (
  <View style={[st.card, style]}>{children}</View>
);

export function Skeleton({ h = 16, w = "100%", style }: { h?: number; w?: number | `${number}%`; style?: StyleProp<ViewStyle> }) {
  const o = useRef(new Animated.Value(0.5)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(o, { toValue: 1, duration: 700, useNativeDriver: true }),
        Animated.timing(o, { toValue: 0.5, duration: 700, useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [o]);
  return <Animated.View style={[{ height: h, width: w, borderRadius: R.sm, backgroundColor: C.sunken, opacity: o }, style]} />;
}

const STATUS: Record<OfferStatus, { icon: IconName; fg: string; bg: string }> = {
  sent: { icon: "time-outline", fg: C.earth, bg: C.earthSoft },
  accepted: { icon: "checkmark-circle", fg: C.primary, bg: C.primarySoft },
  rejected: { icon: "close-circle-outline", fg: C.danger, bg: C.dangerSoft },
};
export function StatusPill({ status }: { status: OfferStatus }) {
  const { t } = useSession();
  const s = STATUS[status];
  return (
    <View style={[st.pill, { backgroundColor: s.bg }]}>
      <Icon name={s.icon} size={14} color={s.fg} />
      <Txt v="caption" w="s" color={s.fg}>
        {t(`status_${status}`)}
      </Txt>
    </View>
  );
}

export function Field({
  label,
  hint,
  error,
  ...input
}: { label: string; hint?: string; error?: string | null } & TextInputProps) {
  const { lang } = useSession();
  return (
    <View style={{ gap: 6 }}>
      <Txt v="label">{label}</Txt>
      <TextInput
        accessibilityLabel={label}
        accessibilityHint={hint}
        placeholderTextColor={C.faint}
        style={[st.input, { fontFamily: lang === "en" ? FONTS.latin.r : FONTS.deva.r }, error ? { borderColor: C.danger } : null]}
        {...input}
      />
      {error ? <Notice kind="error" text={error} /> : hint ? <Txt v="caption" color={C.muted}>{hint}</Txt> : null}
    </View>
  );
}

export function Notice({ kind = "info", text }: { kind?: "info" | "error" | "success"; text: string }) {
  const m = {
    info: { icon: "information-circle-outline" as IconName, fg: C.muted },
    error: { icon: "alert-circle-outline" as IconName, fg: C.danger },
    success: { icon: "checkmark-circle-outline" as IconName, fg: C.primary },
  }[kind];
  return (
    <View style={{ flexDirection: "row", gap: 6, alignItems: "flex-start" }} accessibilityLiveRegion={kind === "error" ? "polite" : "none"}>
      <View style={{ paddingTop: 2 }}>
        <Icon name={m.icon} size={16} color={m.fg} />
      </View>
      <Txt v="small" color={m.fg} style={{ flex: 1 }}>
        {text}
      </Txt>
    </View>
  );
}

export function LangSwitch() {
  const { lang, setLang, t } = useSession();
  return (
    <View style={st.seg} accessibilityRole="radiogroup" accessibilityLabel={t("language")}>
      {LANGS.map((l) => (
        <Pressable
          key={l.code}
          onPress={() => setLang(l.code)}
          accessibilityRole="radio"
          accessibilityState={{ checked: lang === l.code }}
          accessibilityLabel={l.label}
          style={[st.segItem, lang === l.code && { backgroundColor: C.surface, borderColor: C.border, borderWidth: 1 }]}
        >
          <Text style={{ fontFamily: l.code === "en" ? FONTS.latin.s : FONTS.deva.s, fontSize: 15, color: lang === l.code ? C.primary : C.muted }}>
            {l.label}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

export function StateView({
  icon,
  title,
  body,
  action,
  onAction,
}: {
  icon: IconName;
  title: string;
  body?: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <View style={{ alignItems: "center", paddingVertical: S.xxl, paddingHorizontal: S.xl, gap: S.sm }}>
      <View style={st.stateIcon}>
        <Icon name={icon} size={26} color={C.muted} />
      </View>
      <Txt v="h2" style={{ textAlign: "center" }}>
        {title}
      </Txt>
      {body ? (
        <Txt v="small" color={C.muted} style={{ textAlign: "center" }}>
          {body}
        </Txt>
      ) : null}
      {action && onAction ? <Button label={action} onPress={onAction} kind="secondary" style={{ marginTop: S.sm }} /> : null}
    </View>
  );
}

/** Bottom sheet (filters, sort). Tapping outside or Android back closes it. */
export function Sheet({ visible, title, onClose, children, footer }: { visible: boolean; title: string; onClose: () => void; children: ReactNode; footer?: ReactNode }) {
  const insets = useSafeAreaInsets();
  const { t } = useSession();
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <Pressable style={{ flex: 1, backgroundColor: "rgba(20,24,18,0.45)" }} onPress={onClose} accessibilityRole="button" accessibilityLabel={t("close")} />
        <View style={{ backgroundColor: C.bg, borderTopLeftRadius: 20, borderTopRightRadius: 20, maxHeight: "88%" }}>
          <View style={{ alignSelf: "center", width: 40, height: 4, borderRadius: 2, backgroundColor: C.border, marginTop: S.sm }} />
          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: S.xl, paddingTop: S.md }}>
            <Txt v="title" accessibilityRole="header">
              {title}
            </Txt>
            <Pressable onPress={onClose} hitSlop={10} accessibilityRole="button" accessibilityLabel={t("close")} style={{ minWidth: TOUCH, minHeight: TOUCH, alignItems: "flex-end", justifyContent: "center" }}>
              <Icon name="close" size={24} color={C.muted} />
            </Pressable>
          </View>
          <ScrollView contentContainerStyle={{ padding: S.xl, gap: S.lg }} keyboardShouldPersistTaps="handled">
            {children}
          </ScrollView>
          {footer ? <View style={{ padding: S.lg, paddingBottom: S.lg + insets.bottom, borderTopWidth: 1, borderTopColor: C.border }}>{footer}</View> : <View style={{ height: insets.bottom }} />}
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

export const Row = ({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) => (
  <View style={[{ flexDirection: "row", alignItems: "center", gap: S.sm }, style]}>{children}</View>
);

export const st = StyleSheet.create({
  btn: {
    minHeight: 50,
    borderRadius: R.md,
    paddingHorizontal: S.lg,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: S.sm,
  },
  chip: {
    minHeight: 40,
    paddingHorizontal: 14,
    borderRadius: R.pill,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  card: { backgroundColor: C.surface, borderRadius: R.lg, borderWidth: 1, borderColor: C.border, padding: S.lg },
  pill: { flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 8, paddingVertical: 3, borderRadius: R.pill, alignSelf: "flex-start" },
  input: {
    minHeight: 50,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: R.md,
    backgroundColor: C.surface,
    paddingHorizontal: 14,
    fontSize: 16,
    color: C.text,
  },
  seg: { flexDirection: "row", backgroundColor: C.sunken, borderRadius: R.md, padding: 3, gap: 3 },
  segItem: { flex: 1, minHeight: TOUCH, alignItems: "center", justifyContent: "center", borderRadius: R.sm, borderWidth: 1, borderColor: "transparent" },
  stateIcon: { width: 56, height: 56, borderRadius: 28, backgroundColor: C.sunken, alignItems: "center", justifyContent: "center", marginBottom: S.xs },
});
