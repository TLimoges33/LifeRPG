import React, { useEffect, useState } from 'react';
import { View, Text, Button } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { auth } from '../lib/auth';

export default function Home() {
    const nav = useNavigation<any>();
    const [hasToken, setHasToken] = useState(false);
    useEffect(() => {
        auth.getTokens().then(t => setHasToken(!!t?.accessToken));
    }, []);
    const onLogout = async () => {
        await auth.revoke();
        nav.reset({ index: 0, routes: [{ name: 'Login' }] });
    };
    return (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <Text>Home Screen (habits list)</Text>
            <Text>{hasToken ? 'Signed in' : 'No token found'}</Text>
            <Button title="Logout" onPress={onLogout} />
        </View>
    );
}
