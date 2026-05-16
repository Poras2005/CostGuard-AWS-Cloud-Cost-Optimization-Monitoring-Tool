import logging
from datetime import datetime, timedelta, date
from shared.aws_client import client

log = logging.getLogger('costguard.cost_analyzer')

def get_daily_cost_by_service(creds, lookback_days=8):
    # CE is a global service, but its API endpoint is only available in us-east-1
    ce = client('ce', creds, region='us-east-1') 
    
    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)
    
    resp = ce.get_cost_and_usage(
        TimePeriod={'Start': str(start_date), 'End': str(end_date)},
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )
    
    result = {}
    for period in resp['ResultsByTime']:
        for group in period['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            if service not in result:
                result[service] = []
            result[service].append(cost)
            
    return result

def get_total_cost_last_n_days(creds, days=30):
    ce = client('ce', creds, region='us-east-1')
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    resp = ce.get_cost_and_usage(
        TimePeriod={'Start': str(start_date), 'End': str(end_date)},
        Granularity='DAILY',
        Metrics=['UnblendedCost']
    )
    
    return [
        {'date': p['TimePeriod']['Start'], 'cost': float(p['Total']['UnblendedCost']['Amount'])}
        for p in resp['ResultsByTime']
    ]
