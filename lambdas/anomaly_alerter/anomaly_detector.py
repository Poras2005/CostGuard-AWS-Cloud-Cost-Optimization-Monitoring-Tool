import logging

log = logging.getLogger('costguard.anomaly_detector')

CAUSE_HINTS = {
    'Amazon Elastic Compute Cloud': 'Check for new or running EC2 instances',
    'Amazon Simple Storage Service': 'Check for data transfer or new S3 uploads',
    'Amazon Relational Database Service': 'Check RDS instance size or Multi-AZ changes',
    'AWS Lambda': 'Check for increased invocations or duration',
    'Amazon CloudWatch': 'Check for new dashboards, alarms, or log ingestion',
    'Amazon Elastic Kubernetes Service': 'Check for new node groups or cluster changes',
}

def detect_anomalies(cost_by_service, spike_threshold_pct=20, min_spend=1.0):
    anomalies = []
    
    for service, daily_costs in cost_by_service.items():
        if len(daily_costs) < 2:
            continue
            
        yesterday = daily_costs[-1]
        history = daily_costs[:-1]
        avg = sum(history) / len(history) if history else 0
        
        if yesterday < min_spend and avg < min_spend:
            continue
            
        if avg == 0:
            pct_change = 100.0 if yesterday > 0 else 0.0
        else:
            pct_change = ((yesterday - avg) / avg) * 100
            
        if pct_change >= spike_threshold_pct:
            anomaly = {
                'service'       : service,
                'yesterday_cost': round(yesterday, 4),
                'seven_day_avg' : round(avg, 4),
                'pct_change'    : round(pct_change, 1),
                'likely_cause'  : CAUSE_HINTS.get(service, 'Check AWS console for recent changes'),
            }
            anomalies.append(anomaly)
            
    return sorted(anomalies, key=lambda x: x['pct_change'], reverse=True)
