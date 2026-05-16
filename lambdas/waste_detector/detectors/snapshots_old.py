import logging
from datetime import datetime, timezone, timedelta
from shared.aws_client import client

log = logging.getLogger('costguard.snapshots_old')

SNAPSHOT_COST_PER_GB_MONTH = 0.05

def detect_old_snapshots(creds, account_id, age_days=30):
    ec2 = client('ec2', creds)
    cutoff = datetime.now(timezone.utc) - timedelta(days=age_days)
    waste = []

    paginator = ec2.get_paginator('describe_snapshots')
    pages = paginator.paginate(OwnerIds=[account_id])

    for page in pages:
        for snap in page['Snapshots']:
            if snap['StartTime'] < cutoff:
                size_gb = snap['VolumeSize']
                monthly_cost = size_gb * SNAPSHOT_COST_PER_GB_MONTH
                age = (datetime.now(timezone.utc) - snap['StartTime']).days

                item = {
                    'resource_type': 'Snapshot',
                    'resource_id'  : snap['SnapshotId'],
                    'size_gb'      : size_gb,
                    'age_days'     : age,
                    'monthly_cost' : round(monthly_cost, 2),
                    'reason'       : f'Snapshot is {age} days old (>{age_days} days threshold)',
                }
                waste.append(item)

    return waste
