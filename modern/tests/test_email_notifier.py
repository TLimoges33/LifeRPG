import os
from modern.backend.notifier import send_email

def test_email_console_transport(monkeypatch, capsys):
    monkeypatch.setenv('LIFERPG_EMAIL_TRANSPORT', 'console')
    # Should not raise and should log event via metrics logger; we can't capture it easily
    send_email('test@example.com', 'Subj', 'Body')


def test_email_disabled_transport(monkeypatch):
    monkeypatch.setenv('LIFERPG_EMAIL_TRANSPORT', 'disabled')
    send_email('nobody@example.com', 'x', 'y')


def test_email_smtp_missing_host_falls_back(monkeypatch):
    monkeypatch.setenv('LIFERPG_EMAIL_TRANSPORT', 'smtp')
    # no SMTP_HOST set
    send_email('nobody@example.com', 'x', 'y')
