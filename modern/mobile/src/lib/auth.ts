import {
  authorize as rnAuthorize,
  refresh as rnRefresh,
  revoke as rnRevoke,
} from "react-native-app-auth";
import type { AuthorizeResult, RefreshResult } from "react-native-app-auth";
import * as SecureStore from "expo-secure-store";
import * as Crypto from "expo-crypto";
import Constants from "expo-constants";

type Tokens = {
  accessToken: string;
  accessTokenExpirationDate?: string;
  refreshToken?: string;
  idToken?: string;
  tokenType?: string;
};

const SECURE_STORE_KEY = "liferpg.tokens.encrypted";
const ENCRYPTION_KEY_STORE = "liferpg.encryption.key";

// Generate or retrieve app-specific encryption key
async function getOrCreateEncryptionKey(): Promise<string> {
  let key = await SecureStore.getItemAsync(ENCRYPTION_KEY_STORE);
  if (!key) {
    // Generate a new encryption key
    key = await Crypto.digestStringAsync(
      Crypto.CryptoDigestAlgorithm.SHA256,
      `${Constants.installationId}-${Date.now()}-${Math.random()}`,
      { encoding: Crypto.CryptoEncoding.HEX }
    );
    await SecureStore.setItemAsync(ENCRYPTION_KEY_STORE, key, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED,
    });
  }
  return key;
}

// Simple encryption for additional token protection
async function encryptTokens(tokens: Tokens): Promise<string> {
  const key = await getOrCreateEncryptionKey();
  const tokenString = JSON.stringify(tokens);

  // Simple XOR encryption (not cryptographically secure but adds a layer)
  const encrypted = Array.from(tokenString)
    .map((char, i) =>
      String.fromCharCode(char.charCodeAt(0) ^ key.charCodeAt(i % key.length))
    )
    .join("");

  return Buffer.from(encrypted).toString("base64");
}

async function decryptTokens(encryptedData: string): Promise<Tokens | null> {
  try {
    const key = await getOrCreateEncryptionKey();
    const encrypted = Buffer.from(encryptedData, "base64").toString();

    const decrypted = Array.from(encrypted)
      .map((char, i) =>
        String.fromCharCode(char.charCodeAt(0) ^ key.charCodeAt(i % key.length))
      )
      .join("");

    return JSON.parse(decrypted);
  } catch (error) {
    console.warn("Failed to decrypt tokens, clearing storage:", error);
    await clearTokens();
    return null;
  }
}

function getOidcConfig() {
  const extra = (Constants.expoConfig?.extra ||
    Constants.manifest?.extra) as any;
  const oidc = extra?.oidc;
  if (!oidc?.issuer || !oidc?.clientId || !oidc?.redirectUrl) {
    throw new Error("OIDC config missing (issuer/clientId/redirectUrl)");
  }
  return {
    issuer: oidc.issuer,
    clientId: oidc.clientId,
    redirectUrl: oidc.redirectUrl,
    scopes: oidc.scopes || ["openid", "profile", "email", "offline_access"],
    dangerouslyAllowInsecureHttpRequests: false,
    additionalParameters: {},
  } as const;
}

export async function saveTokens(t: Tokens) {
  const encrypted = await encryptTokens(t);
  await SecureStore.setItemAsync(SECURE_STORE_KEY, encrypted, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED,
    requireAuthentication: true, // Require biometric/passcode
  });
}

export async function getTokens(): Promise<Tokens | null> {
  const encrypted = await SecureStore.getItemAsync(SECURE_STORE_KEY);
  if (!encrypted) return null;
  return await decryptTokens(encrypted);
}

export async function clearTokens() {
  await SecureStore.deleteItemAsync(SECURE_STORE_KEY);
  await SecureStore.deleteItemAsync(ENCRYPTION_KEY_STORE);
  // Clear any legacy unencrypted tokens
  await SecureStore.deleteItemAsync("liferpg.tokens");
}

export async function authorize(): Promise<Tokens> {
  const cfg = getOidcConfig();
  const res: AuthorizeResult = await rnAuthorize(cfg as any);
  const tokens: Tokens = {
    accessToken: res.accessToken,
    accessTokenExpirationDate: res.accessTokenExpirationDate,
    refreshToken: res.refreshToken,
    idToken: (res as any).idToken,
    tokenType: res.tokenType,
  };
  await saveTokens(tokens);
  return tokens;
}

export async function refresh(): Promise<Tokens | null> {
  const cfg = getOidcConfig();
  const current = await getTokens();
  if (!current?.refreshToken) return null;
  const res: RefreshResult = await rnRefresh(cfg as any, {
    refreshToken: current.refreshToken,
  });
  const tokens: Tokens = {
    accessToken: res.accessToken,
    accessTokenExpirationDate: res.accessTokenExpirationDate,
    refreshToken: res.refreshToken || current.refreshToken,
    idToken: (res as any).idToken,
    tokenType: res.tokenType,
  };
  await saveTokens(tokens);
  return tokens;
}

export async function revoke(): Promise<void> {
  const cfg = getOidcConfig();
  const current = await getTokens();
  try {
    if (current?.accessToken)
      await rnRevoke(cfg as any, {
        tokenToRevoke: current.accessToken,
        sendClientId: true,
      });
    if (current?.refreshToken)
      await rnRevoke(cfg as any, {
        tokenToRevoke: current.refreshToken,
        sendClientId: true,
      });
  } finally {
    await clearTokens();
  }
}

export const auth = { authorize, refresh, revoke, getTokens, clearTokens };

// Enhanced auth manager for better integration
export const authManager = {
  async login() {
    return await authorize();
  },

  async logout() {
    await revoke();
  },

  async getTokenInfo() {
    return await getTokens();
  },

  isTokenExpired(tokenInfo: Tokens): boolean {
    if (!tokenInfo.accessTokenExpirationDate) {
      return false; // If no expiration date, assume not expired
    }

    const expirationTime = new Date(
      tokenInfo.accessTokenExpirationDate
    ).getTime();
    const currentTime = Date.now();

    // Add 5-minute buffer before expiration
    return currentTime >= expirationTime - 5 * 60 * 1000;
  },

  async refreshTokenIfNeeded(): Promise<Tokens | null> {
    const current = await getTokens();
    if (!current) return null;

    if (this.isTokenExpired(current)) {
      return await refresh();
    }

    return current;
  },

  async getValidToken(): Promise<string | null> {
    const tokenInfo = await this.refreshTokenIfNeeded();
    return tokenInfo?.accessToken || null;
  },
};
