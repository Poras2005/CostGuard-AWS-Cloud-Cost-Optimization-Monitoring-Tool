import json, logging, os, yaml
from pathlib import Path
from shared.aws_client import get_creds
from shared.notifier import Notifier
from cost_analyzer import get_daily_cost_by_service
from anomaly_detector import detect_anomalies

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('costguard.anomaly_alerter')

def load_config():
    path = Path(__file__).parent.parent.parent / 'config.yaml'
    if path.exists():
        return yaml.safe_load(open(path))
    return {}

def lambda_handler(event, context):
    cfg = load_config()
    creds = get_creds()
    
    # Load settings from config.yaml
    aa_cfg = cfg.get('anomaly_alerter', {})
    lookback = aa_cfg.get('lookback_days', 8)
    threshold = aa_cfg.get('spike_threshold_percent', 20)
    min_spend = aa_cfg.get('min_spend_to_alert', 1.0)
    
    notifier = Notifier(
        creds,
        slack_webhook = os.environ.get('SLACK_WEBHOOK', ''),
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN', '')
    )
    
    # Fetch cost data
    cost_data = get_daily_cost_by_service(creds, lookback_days=lookback)
    
    # Detect anomalies
    anomalies = detect_anomalies(cost_data, threshold, min_spend)
    
    if not anomalies:
        log.info("No cost anomalies detected.")
        return {'statusCode': 200, 'anomalies': 0}
        
    # Format report
    lines = [f'Detected {len(anomalies)} cost anomaly(s) in your AWS account:', '']
    
    for a in anomalies:
        lines.append(f" {a['service']}")
        lines.append(f"  Yesterday : ${a['yesterday_cost']:.4f}")
        lines.append(f"  7-day avg : ${a['seven_day_avg']:.4f}")
        lines.append(f"  Spike     : +{a['pct_change']}%")
        lines.append(f"  Hint      : {a['likely_cause']}")
        lines.append('')
        
    message = '\n'.join(lines)
    
    # Send notifications
    notifier.send(
        subject=f'CostGuard Alert — {len(anomalies)} Cost Anomaly(s) Detected',
        message=message
    )
    
    return {
        'statusCode': 200,
        'anomalies': len(anomalies),
        'details': anomalies
    }

if __name__ == '__main__':
    # Local execution mock
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2, default=str))
