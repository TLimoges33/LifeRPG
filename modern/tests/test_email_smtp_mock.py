def test_send_email_via_mock_smtp(monkeypatch):
    import os
    os.environ['LIFERPG_EMAIL_TRANSPORT'] = 'smtp'
    os.environ['SMTP_HOST'] = 'localhost'
    os.environ['SMTP_PORT'] = '2525'
    os.environ['SMTP_USERNAME'] = 'user'
    os.environ['SMTP_PASSWORD'] = 'pass'
    os.environ['SMTP_USE_TLS'] = 'false'

    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=10):
            assert host == 'localhost'
            assert int(port) == 2525
            self.logged_in = False
        def starttls(self):
            # should not be called since SMTP_USE_TLS=false
            pass
        def login(self, user, pwd):
            assert user == 'user' and pwd == 'pass'
            self.logged_in = True
        def send_message(self, msg):
            sent['from'] = msg['From']
            sent['to'] = msg['To']
            sent['subject'] = msg['Subject']
            sent['body'] = msg.get_content()
        def quit(self):
            pass

    import smtplib
    monkeypatch.setattr(smtplib, 'SMTP', FakeSMTP)

    # Rebuild settings to pick up envs
    import importlib
    import modern.backend.config as config
    importlib.reload(config)
    # Patch config.settings inside notifier to this new instance
    import modern.backend.notifier as notifier
    notifier.settings = config.settings

    notifier.send_email('to@example.com', 'Hello', 'Body text')
    assert sent.get('to') == 'to@example.com'
    assert sent.get('subject') == 'Hello'
    assert 'Body text' in (sent.get('body') or '')
