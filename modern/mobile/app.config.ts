import type { ExpoConfig } from 'expo/config';

const OIDC_ISSUER = process.env.EXPO_PUBLIC_OIDC_ISSUER || 'https://example-idp.com/realms/liferpg';
const OIDC_CLIENT_ID = process.env.EXPO_PUBLIC_OIDC_CLIENT_ID || 'liferpg-mobile';
const OIDC_REDIRECT = process.env.EXPO_PUBLIC_OIDC_REDIRECT || 'liferpg:/oauthredirect';
const OIDC_SCOPES = (process.env.EXPO_PUBLIC_OIDC_SCOPES || 'openid profile email offline_access').split(' ');
const API_BASE = process.env.EXPO_PUBLIC_API_BASE_URL || 'https://api.example.com';

function toUrl(maybe: string): URL | null {
    try {
        if (/^[a-z][a-z0-9+.-]*:\/\//i.test(maybe)) return new URL(maybe);
        if (/^[a-z][a-z0-9+.-]*:\/[^/]/i.test(maybe)) return new URL(maybe.replace(':/', '://'));
        return null;
    } catch {
        return null;
    }
}

const parsedRedirect = toUrl(OIDC_REDIRECT);

const config: ExpoConfig = {
    name: 'LifeRPG Mobile',
    slug: 'liferpg-mobile',
    scheme: 'liferpg',
    version: '0.0.1',
    orientation: 'portrait',
    platforms: ['android', 'ios'],
    // Use repo image as icon until dedicated asset exists
    icon: '../../Res/128px-Role-playing_video_game_icon.svg.png',
    userInterfaceStyle: 'automatic',
    updates: { enabled: true },
    extra: {
        oidc: {
            issuer: OIDC_ISSUER,
            clientId: OIDC_CLIENT_ID,
            redirectUrl: OIDC_REDIRECT,
            scopes: OIDC_SCOPES,
        },
        apiBaseUrl: API_BASE,
    },
    ios: {
        bundleIdentifier: 'com.liferpg.mobile',
        associatedDomains: [],
    },
    android: {
        package: 'com.liferpg.mobile',
        intentFilters: [
            {
                action: 'VIEW',
                autoVerify: false,
                category: ['BROWSABLE', 'DEFAULT'],
                data: [
                    parsedRedirect
                        ? ((() => {
                            const base: any = { scheme: parsedRedirect.protocol.replace(':', '') };
                            if (parsedRedirect.host) base.host = parsedRedirect.host;
                            const path = parsedRedirect.pathname;
                            if (path && path !== '/') base.path = path;
                            return base;
                        })())
                        : { scheme: 'liferpg', host: 'oauthredirect' },
                ],
            },
        ],
    },
    experiments: {
        // Keep default
    },
};

export default config;
