import logging
from lambdas.anomaly_alerter.cost_analyzer import get_daily_cost_by_service, get_total_cost_last_n_days
from lambdas.waste_detector.detectors.ec2_idle import detect_idle_ec2
from lambdas.waste_detector.detectors.ebs_unused import detect_unused_ebs
from lambdas.waste_detector.detectors.eip_unused import detect_unused_eips
from lambdas.waste_detector.detectors.snapshots_old import detect_old_snapshots
import os

log = logging.getLogger('costguard.data_fetcher')

def fetch_dashboard_data(creds, account_id):
    # 1. Get Monthly Trend (30 days)
    daily_spend = get_total_cost_last_n_days(creds, days=30)
    total_cost = sum(d['cost'] for d in daily_spend)
    
    # 2. Get Top 5 Services
    service_costs = get_daily_cost_by_service(creds, lookback_days=30)
    top_services = []
    for svc, costs in service_costs.items():
        top_services.append({'service': svc, 'cost': sum(costs)})
    top_services = sorted(top_services, key=lambda x: x['cost'], reverse=True)[:5]
    
    # 3. Get Waste Summary
    waste_items = []
    waste_items += detect_idle_ec2(creds)
    waste_items += detect_unused_ebs(creds)
    waste_items += detect_unused_eips(creds)
    if account_id:
        waste_items += detect_old_snapshots(creds, account_id)
        
    # 4. Get Anomaly Count (last 24h)
    from lambdas.anomaly_alerter.anomaly_detector import detect_anomalies
    anomalies = detect_anomalies(service_costs)
    
    return {
        'total_cost': total_cost,
        'daily_costs': daily_spend,
        'top_services': top_services,
        'waste_items': waste_items,
        'anomaly_count': len(anomalies)
    }
