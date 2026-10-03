import { useFocusEffect } from "expo-router";
import { useCallback, useRef } from "react";
import { AppState } from "react-native";

/** Run `fn` when the screen gains focus, then every `ms` while it stays focused and the app is in the foreground. */
export function usePoll(fn: () => void, ms = 20000, enabled = true) {
  const ref = useRef(fn);
  ref.current = fn;
  useFocusEffect(
    useCallback(() => {
      if (!enabled) return;
      ref.current();
      const timer = setInterval(() => {
        if (AppState.currentState === "active") ref.current();
      }, ms);
      const sub = AppState.addEventListener("change", (s) => s === "active" && ref.current());
      return () => {
        clearInterval(timer);
        sub.remove();
      };
    }, [ms, enabled]),
  );
}
