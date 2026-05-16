import logging
from datetime import datetime, timedelta, timezone
from shared.aws_client import client

log = logging.getLogger('costguard.ec2_idle')

# Cost per hour for t2.micro in ap-south-1 (update as needed)
EC2_HOURLY_COSTS = {
    't2.micro'  : 0.0116,
    't2.small'  : 0.023,
    't2.medium' : 0.0464,
    't3.micro'  : 0.0104,
    't3.small'  : 0.0208,
    't3.medium' : 0.0416,
    'm5.large'  : 0.096,
    'm5.xlarge' : 0.192,
    'default'   : 0.05
}

def detect_idle_ec2(creds, cpu_threshold=5, lookback_days=7, dry_run=True, auto_stop=False):
    ec2 = client('ec2', creds)
    cw = client('cloudwatch', creds)
    waste = []

    resp = ec2.describe_instances(
        Filters=[{'Name':'instance-state-name','Values':['running']}]
    )

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)

    for reservation in resp['Reservations']:
        for inst in reservation['Instances']:
            instance_id = inst['InstanceId']
            instance_type = inst['InstanceType']
            name = next((t['Value'] for t in inst.get('Tags',[]) if t['Key']=='Name'), 'unnamed')

            metrics = cw.get_metric_statistics(
                Namespace ='AWS/EC2',
                MetricName ='CPUUtilization',
                Dimensions =[{'Name':'InstanceId','Value':instance_id}],
                StartTime =start,
                EndTime =end,
                Period =86400,
                Statistics =['Average']
            )

            if not metrics['Datapoints']:
                continue

            avg_cpu = sum(d['Average'] for d in metrics['Datapoints']) / len(metrics['Datapoints'])

            if avg_cpu < cpu_threshold:
                hourly = EC2_HOURLY_COSTS.get(instance_type, EC2_HOURLY_COSTS['default'])
                monthly_cost = hourly * 24 * 30
                
                item = {
                    'resource_type': 'EC2',
                    'resource_id'  : instance_id,
                    'name'         : name,
                    'instance_type': instance_type,
                    'avg_cpu_pct'  : round(avg_cpu, 2),
                    'monthly_cost' : round(monthly_cost, 2),
                    'reason'       : f'Avg CPU {avg_cpu:.1f}% over {lookback_days} days',
                }

                waste.append(item)

                if auto_stop and not dry_run:
                    ec2.stop_instances(InstanceIds=[instance_id])
                    item['action'] = 'stopped'
                else:
                    item['action'] = 'dry_run' if dry_run else 'reported'

    return waste
