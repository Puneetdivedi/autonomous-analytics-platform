import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from 'react';
import { authService } from '@/services/authService';
import { getAccessToken } from '@/services/apiClient';
import { LoginPayload, RegisterPayload, User, UserRole } from '@/types';

export interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  /** True when no backend is reachable — the app runs in local demo mode. */
  demoMode: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const LOCAL_GUEST: User = {
  id: 'local-guest',
  email: 'guest@demo',
  full_name: 'Guest',
  role: UserRole.ANALYST,
};

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined
);

// Sign-in is disabled: the app provisions a per-browser guest account so users
// land straight in the workspace. The credentials are generated once and kept in
// localStorage so the same browser keeps the same projects/chats across visits.
const GUEST_KEY = 'ada_guest';

interface GuestCreds {
  email: string;
  password: string;
  full_name: string;
}

function guestCredentials(): GuestCreds {
  const existing = localStorage.getItem(GUEST_KEY);
  if (existing) {
    try {
      return JSON.parse(existing) as GuestCreds;
    } catch {
      /* fall through and regenerate */
    }
  }
  const id = Math.random().toString(36).slice(2, 10);
  const creds: GuestCreds = {
    email: `guest_${id}@demo.eaap.io`,
    password: `Guest!${id}${id}`,
    full_name: 'Guest',
  };
  localStorage.setItem(GUEST_KEY, JSON.stringify(creds));
  return creds;
}

async function ensureGuestSession(): Promise<void> {
  const creds = guestCredentials();
  try {
    await authService.login({ email: creds.email, password: creds.password });
    return;
  } catch {
    /* not registered yet — create it, then log in */
  }
  try {
    await authService.register({
      email: creds.email,
      password: creds.password,
      full_name: creds.full_name,
      role: UserRole.ANALYST,
    });
  } catch {
    /* already exists / race — proceed to login */
  }
  await authService.login({ email: creds.email, password: creds.password });
}

async function tryMe(): Promise<User | null> {
  try {
    return await authService.me();
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [demoMode, setDemoMode] = useState<boolean>(false);

  const refreshUser = useCallback(async () => {
    const me = await tryMe();
    setUser(me);
  }, []);

  // Bootstrap: reuse a session, else auto-provision a guest. If the backend is
  // unreachable, fall back to a local guest so the app still opens (demo mode).
  const bootstrap = useCallback(async () => {
    setLoading(true);
    try {
      let me = getAccessToken() ? await tryMe() : null;
      if (!me) {
        await ensureGuestSession();
        me = await tryMe();
      }
      if (me) {
        setUser(me);
        setDemoMode(false);
      } else {
        setUser(LOCAL_GUEST);
        setDemoMode(true);
      }
    } catch {
      setUser(LOCAL_GUEST);
      setDemoMode(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const login = useCallback(
    async (payload: LoginPayload) => {
      await authService.login(payload);
      await refreshUser();
    },
    [refreshUser]
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      await authService.register(payload);
      await authService.login({
        email: payload.email,
        password: payload.password,
      });
      await refreshUser();
    },
    [refreshUser]
  );

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
    // Re-provision a guest immediately so the app never lands on a sign-in wall.
    void bootstrap();
  }, [bootstrap]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      demoMode,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, loading, demoMode, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
