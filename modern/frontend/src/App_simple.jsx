import React from 'react';

console.log('🧙‍♂️ App_simple.jsx loaded successfully!');

const App = () => {
    console.log('🔮 App component rendering...');

    React.useEffect(() => {
        console.log('✨ App component mounted successfully!');

        // Test API connection
        fetch('/api/v1/health')
            .then(response => response.json())
            .then(data => {
                console.log('🌟 API health check:', data);
            })
            .catch(error => {
                console.error('❌ API health check failed:', error);
            });
    }, []);

    return (
        <div style={{
            background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)',
            minHeight: '100vh',
            color: '#e0e0e0',
            padding: '20px',
            fontFamily: 'system-ui, sans-serif'
        }}>
            <h1 style={{
                color: '#ffd700',
                textAlign: 'center',
                fontSize: '2.5rem',
                marginBottom: '20px'
            }}>
                🧙‍♂️ The Wizard's Grimoire
            </h1>

            <div style={{
                textAlign: 'center',
                fontSize: '1.2rem',
                marginBottom: '30px'
            }}>
                ✨ React is working! The magical energies are flowing! ✨
            </div>

            <div style={{
                background: 'rgba(124, 58, 237, 0.2)',
                border: '2px solid #7c3aed',
                borderRadius: '12px',
                padding: '20px',
                maxWidth: '600px',
                margin: '0 auto',
                textAlign: 'center'
            }}>
                <h2 style={{ color: '#c084fc', marginBottom: '15px' }}>System Status</h2>
                <p>✅ React Component Mounted</p>
                <p>✅ CSS Styles Applied</p>
                <p>✅ JavaScript Running</p>

                <button
                    style={{
                        background: 'linear-gradient(135deg, #7c3aed, #c084fc)',
                        border: 'none',
                        borderRadius: '8px',
                        color: 'white',
                        padding: '12px 24px',
                        fontSize: '1rem',
                        cursor: 'pointer',
                        marginTop: '15px'
                    }}
                    onClick={() => alert('🪄 Magic button clicked!')}
                >
                    Cast Test Spell
                </button>
            </div>

            <div style={{
                marginTop: '30px',
                textAlign: 'center',
                fontSize: '0.9rem',
                opacity: 0.7
            }}>
                If you see this message, React is rendering correctly!
            </div>
        </div>
    );
};

export default App;
