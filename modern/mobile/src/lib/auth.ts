import { authorize as rnAuthorize, refresh as rnRefresh, revoke as rnRevoke } from 'react-native-app-auth';
import type { AuthorizeResult, RefreshResult } from 'react-native-app-auth';
import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';

type Tokens = {
    accessToken: string;
    accessTokenExpirationDate?: string;
    refreshToken?: string;
    idToken?: string;
    tokenType?: string;
};

const SECURE_STORE_KEY = 'liferpg.tokens';

function getOidcConfig() {
    const extra = (Constants.expoConfig?.extra || Constants.manifest?.extra) as any;
    const oidc = extra?.oidc;
    if (!oidc?.issuer || !oidc?.clientId || !oidc?.redirectUrl) {
        throw new Error('OIDC config missing (issuer/clientId/redirectUrl)');
    }
    return {
        issuer: oidc.issuer,
        clientId: oidc.clientId,
        redirectUrl: oidc.redirectUrl,
        scopes: oidc.scopes || ['openid', 'profile', 'email', 'offline_access'],
        dangerouslyAllowInsecureHttpRequests: false,
        additionalParameters: {},
    } as const;
}

export async function saveTokens(t: Tokens) {
    await SecureStore.setItemAsync(SECURE_STORE_KEY, JSON.stringify(t), { keychainAccessible: SecureStore.WHEN_UNLOCKED });
}

export async function getTokens(): Promise<Tokens | null> {
    const raw = await SecureStore.getItemAsync(SECURE_STORE_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

export async function clearTokens() {
    await SecureStore.deleteItemAsync(SECURE_STORE_KEY);
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
    const res: RefreshResult = await rnRefresh(cfg as any, { refreshToken: current.refreshToken });
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
        if (current?.accessToken) await rnRevoke(cfg as any, { tokenToRevoke: current.accessToken, sendClientId: true });
        if (current?.refreshToken) await rnRevoke(cfg as any, { tokenToRevoke: current.refreshToken, sendClientId: true });
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

        const expirationTime = new Date(tokenInfo.accessTokenExpirationDate).getTime();
        const currentTime = Date.now();

        // Add 5-minute buffer before expiration
        return currentTime >= (expirationTime - 5 * 60 * 1000);
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
    }
};
