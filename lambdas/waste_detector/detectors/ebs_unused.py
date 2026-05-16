import logging
from shared.aws_client import client

log = logging.getLogger('costguard.ebs_unused')

EBS_COST_PER_GB_MONTH = 0.10 # gp2 in ap-south-1

def detect_unused_ebs(creds):
    ec2 = client('ec2', creds)
    waste = []

    resp = ec2.describe_volumes(
        Filters=[{'Name':'status','Values':['available']}]
    )

    for vol in resp['Volumes']:
        size_gb = vol['Size']
        monthly_cost = size_gb * EBS_COST_PER_GB_MONTH
        name = next((t['Value'] for t in vol.get('Tags',[]) if t['Key']=='Name'), 'unnamed')

        item = {
            'resource_type': 'EBS',
            'resource_id'  : vol['VolumeId'],
            'name'         : name,
            'size_gb'      : size_gb,
            'volume_type'  : vol['VolumeType'],
            'monthly_cost' : round(monthly_cost, 2),
            'reason'       : 'Unattached (state=available)',
        }

        waste.append(item)

    return waste
