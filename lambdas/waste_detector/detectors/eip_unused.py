import logging
from shared.aws_client import client

log = logging.getLogger('costguard.eip_unused')

EIP_MONTHLY_COST = 3.65 # $0.005/hr when unassociated

def detect_unused_eips(creds):
    ec2 = client('ec2', creds)
    waste = []

    resp = ec2.describe_addresses()

    for addr in resp['Addresses']:
        if 'AssociationId' not in addr:
            item = {
                'resource_type': 'ElasticIP',
                'resource_id'  : addr.get('AllocationId', 'N/A'),
                'public_ip'    : addr['PublicIp'],
                'monthly_cost' : EIP_MONTHLY_COST,
                'reason'       : 'Unassociated Elastic IP',
            }
            waste.append(item)

    return waste
