import React, { useState } from 'react';
import { View, Text, Button, ActivityIndicator } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../App';
import { auth } from '../lib/auth';

type Props = NativeStackScreenProps<RootStackParamList, 'Login'>;

export default function Login({ navigation }: Props) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const onAuthorize = async () => {
        setError(null);
        setLoading(true);
        try {
            const res = await auth.authorize();
            if (res?.accessToken) {
                navigation.replace('Home');
            } else {
                setError('Authorization failed');
            }
        } catch (e: any) {
            setError(e?.message || 'Authorization error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <Text>Login Screen</Text>
            {error ? <Text style={{ color: 'red' }}>{error}</Text> : null}
            {loading ? (
                <ActivityIndicator />
            ) : (
                <Button title="Sign in with OIDC" onPress={onAuthorize} />
            )}
        </View>
    );
}
