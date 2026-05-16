import json, logging, os, yaml
from pathlib import Path
from shared.aws_client import get_creds
from shared.notifier import Notifier
from detectors.ec2_idle import detect_idle_ec2
from detectors.ebs_unused import detect_unused_ebs
from detectors.eip_unused import detect_unused_eips
from detectors.snapshots_old import detect_old_snapshots

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('costguard.waste_detector')

def load_config():
    path = Path(__file__).parent.parent.parent / 'config.yaml'
    if path.exists():
        return yaml.safe_load(open(path))
    return {}

def lambda_handler(event, context):
    cfg = load_config()
    creds = get_creds()
    
    account_id = os.environ.get('AWS_ACCOUNT_ID', '')
    
    # Load settings from config.yaml
    wd_cfg = cfg.get('waste_detector', {})
    dry_run = wd_cfg.get('dry_run', True)
    auto_stop = wd_cfg.get('auto_stop_idle_ec2', False)
    cpu_thresh = wd_cfg.get('ec2_cpu_threshold_percent', 5)
    snap_age = wd_cfg.get('snapshot_age_days', 30)

    notifier = Notifier(
        creds,
        slack_webhook = os.environ.get('SLACK_WEBHOOK', ''),
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN', '')
    )

    all_waste = []
    
    # 1. Detect Idle EC2
    all_waste += detect_idle_ec2(creds, cpu_thresh, dry_run=dry_run, auto_stop=auto_stop)
    
    # 2. Detect Unused EBS
    all_waste += detect_unused_ebs(creds)
    
    # 3. Detect Unused EIPs
    all_waste += detect_unused_eips(creds)
    
    # 4. Detect Old Snapshots
    if account_id:
        all_waste += detect_old_snapshots(creds, account_id, snap_age)

    if not all_waste:
        log.info("No wasted resources found.")
        return {'statusCode': 200, 'waste_count': 0}

    # Format report
    total_monthly = sum(w.get('monthly_cost', 0) for w in all_waste)
    total_annual = total_monthly * 12
    
    lines = [f'Found {len(all_waste)} wasted resources — ${total_monthly:.2f}/mo (${total_annual:.0f}/yr)', '']
    
    for w in all_waste:
        cost = w.get('monthly_cost', 0)
        lines.append(f" {w['resource_type']:12s} {w['resource_id']:25s} ${cost:.2f}/mo — {w['reason']}")

    if dry_run:
        lines.append('')
        lines.append('DRY RUN: No actions taken.')

    message = '\n'.join(lines)
    
    # Send notifications
    notifier.send(
        subject=f'CostGuard Waste Report — ${total_monthly:.2f}/mo wasted',
        message=message
    )

    return {
        'statusCode': 200,
        'waste_count': len(all_waste),
        'total_monthly': total_monthly
    }

if __name__ == '__main__':
    # Local execution mock
    print(json.dumps(lambda_handler({}, None), indent=2, default=str))
