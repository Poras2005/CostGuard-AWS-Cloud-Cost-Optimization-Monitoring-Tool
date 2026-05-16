import requests, logging
from shared.aws_client import client

log = logging.getLogger('costguard.notifier')

class Notifier:
    def __init__(self, creds, slack_webhook='', sns_topic_arn=''):
        self.creds = creds
        self.slack_webhook = slack_webhook
        self.sns_topic_arn = sns_topic_arn

    def send(self, subject, message):
        self._slack(subject, message)
        self._sns(subject, message)

    def _slack(self, subject, message):
        if not self.slack_webhook:
            return
        try:
            payload = {'text': f'*{subject}*\n{message}'}
            requests.post(self.slack_webhook, json=payload, timeout=5)
            log.info('Slack notification sent')
        except Exception as e:
            log.warning(f'Slack failed (non-fatal): {e}')

    def _sns(self, subject, message):
        if not self.sns_topic_arn:
            return
        try:
            sns = client('sns', self.creds)
            sns.publish(
                TopicArn=self.sns_topic_arn,
                Subject=subject[:100],
                Message=message
            )
            log.info('SNS notification sent')
        except Exception as e:
            log.warning(f'SNS failed (non-fatal): {e}')
