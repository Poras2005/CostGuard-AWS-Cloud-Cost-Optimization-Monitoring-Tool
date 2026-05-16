import os, getpass, boto3

def get_creds():
    """
    Returns AWS credentials dict.
    Reads from env vars first (Lambda / CI).
    Falls back to runtime getpass prompt (local dev).
    Credentials are NEVER written to any file.
    """
    key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region = os.environ.get('AWS_REGION', 'ap-south-1')

    if not key_id:
        print('CostGuard — enter AWS credentials (never stored)')
        key_id = getpass.getpass(' AWS Access Key ID : ')
        secret = getpass.getpass(' AWS Secret Access Key : ')

    return {
        'aws_access_key_id' : key_id,
        'aws_secret_access_key': secret,
        'region_name' : region
    }

def client(service, creds, region=None):
    """Create a boto3 client with injected credentials."""
    return boto3.client(service,
        region_name = region or creds['region_name'],
        aws_access_key_id = creds['aws_access_key_id'],
        aws_secret_access_key = creds['aws_secret_access_key'])
