// App-wide state: buyer token (expo-secure-store), cached profile, and the chosen language (persisted).
import * as SecureStore from "expo-secure-store";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, setApiToken, type Buyer } from "./api";
import { cropName, districtName, translate, type Key, type Lang } from "./i18n";

const K = { token: "ss_token", me: "ss_me", lang: "ss_lang" };

type Session = {
  ready: boolean;
  token: string | null;
  me: Buyer | null;
  lang: Lang;
  t: (k: Key, v?: Record<string, string | number>) => string;
  crop: (c: string | null | undefined) => string;
  district: (d: string | null | undefined) => string;
  setLang: (l: Lang) => void;
  signIn: (token: string, me: Buyer) => Promise<void>;
  setMe: (me: Buyer) => void;
  refreshMe: () => Promise<void>;
  signOut: () => Promise<void>;
};

const Ctx = createContext<Session | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [me, setMeState] = useState<Buyer | null>(null);
  const [lang, setLangState] = useState<Lang>("mr");

  const signOut = useCallback(async () => {
    setApiToken(null);
    setToken(null);
    setMeState(null);
    await Promise.all([SecureStore.deleteItemAsync(K.token), SecureStore.deleteItemAsync(K.me)]).catch(() => {});
  }, []);

  const setMe = useCallback((b: Buyer) => {
    setMeState(b);
    SecureStore.setItemAsync(K.me, JSON.stringify(b)).catch(() => {});
  }, []);

  const refreshMe = useCallback(async () => setMe(await api.me()), [setMe]);

  useEffect(() => {
    (async () => {
      try {
        const [tk, cached, lg] = await Promise.all([
          SecureStore.getItemAsync(K.token),
          SecureStore.getItemAsync(K.me),
          SecureStore.getItemAsync(K.lang),
        ]);
        if (lg === "mr" || lg === "hi" || lg === "en") setLangState(lg);
        if (tk) {
          setApiToken(tk, signOut);
          setToken(tk);
          if (cached) setMeState(JSON.parse(cached) as Buyer);
          api.me().then(setMe, () => {}); // fresh profile in the background; a 401 signs out via the hook
        }
      } finally {
        setReady(true);
      }
    })();
  }, [setMe, signOut]);

  const value = useMemo<Session>(
    () => ({
      ready,
      token,
      me,
      lang,
      t: (k, v) => translate(lang, k, v),
      crop: (c) => cropName(lang, c),
      district: (d) => districtName(lang, d),
      setLang: (l) => {
        setLangState(l);
        SecureStore.setItemAsync(K.lang, l).catch(() => {});
      },
      signIn: async (tk, b) => {
        await SecureStore.setItemAsync(K.token, tk).catch(() => {}); // still signed in for this run if the keystore fails
        setApiToken(tk, signOut);
        setToken(tk);
        setMe(b);
      },
      setMe,
      refreshMe,
      signOut,
    }),
    [ready, token, me, lang, setMe, refreshMe, signOut],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession(): Session {
  const s = useContext(Ctx);
  if (!s) throw new Error("useSession outside SessionProvider");
  return s;
}
