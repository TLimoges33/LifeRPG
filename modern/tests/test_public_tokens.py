def test_public_widget_with_token(client):
	# create a user and login
	client.post('/api/v1/users', json={'email': 'pub@example.com'})
	client.post('/api/v1/auth/signup', json={'email': 'pub@example.com', 'password': 'pw'})

	# create a token
	r = client.post('/api/v1/tokens', json={'name': 'widget'})
	assert r.status_code == 200
	tok = r.json()['token']

	# call public status with token
	r2 = client.get(f'/api/v1/public/widgets/status?token={tok}')
	assert r2.status_code == 200
	data = r2.json()
	assert 'active_habits' in data and 'completed_last_7_days' in data and 'current_streak_days' in data

	# invalid token should 401
	r3 = client.get('/api/v1/public/widgets/status?token=bad')
	assert r3.status_code == 401
