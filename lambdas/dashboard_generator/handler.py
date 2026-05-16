import json, logging, os
from shared.aws_client import get_creds, client
from data_fetcher import fetch_dashboard_data
from html_builder import build_html

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('costguard.dashboard')

def lambda_handler(event, context):
    creds = get_creds()
    account_id = os.environ.get('AWS_ACCOUNT_ID', '')
    s3_bucket = os.environ.get('DASHBOARD_BUCKET', '')
    s3_key = os.environ.get('DASHBOARD_KEY', 'index.html')
    
    # 1. Fetch data
    log.info("Fetching dashboard data...")
    data = fetch_dashboard_data(creds, account_id)
    
    # 2. Build HTML
    log.info("Building HTML report...")
    html = build_html(
        total_cost = data['total_cost'],
        top_services = data['top_services'],
        daily_costs = data['daily_costs'],
        waste_items = data['waste_items'],
        anomaly_count = data['anomaly_count']
    )
    
    # 3. Upload to S3
    if s3_bucket:
        log.info(f"Uploading to S3 bucket: {s3_bucket}")
        s3 = client('s3', creds)
        s3.put_object(
            Bucket = s3_bucket,
            Key = s3_key,
            Body = html.encode('utf-8'),
            ContentType = 'text/html'
        )
        url = f"http://{s3_bucket}.s3-website-{creds['region_name']}.amazonaws.com"
        return {'statusCode': 200, 'dashboard_url': url}
    
    return {'statusCode': 200, 'message': 'HTML generated but not uploaded (bucket not set)'}

if __name__ == '__main__':
    # Local test: generate file instead of upload
    creds = {'region_name': 'ap-south-1'} # Dummy
    print("Simulating local dashboard generation...")
    # Mocking data for local preview
    html = build_html(150.50, [], [{'date':'2026-05-01', 'cost':5.0}], [], 0)
    with open('debug_dashboard.html', 'w') as f:
        f.write(html)
    print("Dashboard saved to debug_dashboard.html for preview.")
