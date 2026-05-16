#!/usr/bin/env python3
import argparse, getpass, os, shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / 'dist'

def log(msg): print(f'[costguard] {msg}')

def run(cmd, cwd=None, env=None):
    merged = {**os.environ, **(env or {})}
    r = subprocess.run(cmd, shell=True, cwd=cwd, env=merged)
    if r.returncode != 0: sys.exit(r.returncode)

def get_creds():
    key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
    if not key_id:
        print('CostGuard — enter AWS credentials')
        key_id = getpass.getpass(' AWS Access Key ID : ')
        secret = getpass.getpass(' AWS Secret Access Key : ')
    return key_id, secret

def zip_lambda(name):
    DIST.mkdir(exist_ok=True)
    zip_path = DIST / f'{name}.zip'
    src_dir = ROOT / 'lambdas' / name
    shared = ROOT / 'shared'
    
    log(f'Creating zip: {zip_path.name}')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Pack Lambda source
        for f in src_dir.rglob('*.py'):
            zf.write(f, f.relative_to(src_dir))
        # Pack Shared modules
        for f in shared.rglob('*.py'):
            zf.write(f, Path('shared') / f.relative_to(shared))

def install_deps(name):
    req = ROOT / 'lambdas' / name / 'requirements.txt'
    if not req.exists(): return
    pkg_dir = DIST / f'{name}_pkg'
    log(f'Installing dependencies for {name}...')
    run(f'pip install -r {req} -t {pkg_dir} -q')
    zip_path = DIST / f'{name}.zip'
    with zipfile.ZipFile(zip_path, 'a') as zf:
        for f in pkg_dir.rglob('*'):
            if f.is_file():
                zf.write(f, f.relative_to(pkg_dir))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--destroy', action='store_true')
    parser.add_argument('--invoke', help='waste|anomaly|dashboard')
    args = parser.parse_args()

    # Step 1: Prep artifacts
    if not args.invoke:
        if DIST.exists(): shutil.rmtree(DIST)
        for name in ['waste_detector', 'anomaly_alerter', 'dashboard_generator']:
            if (ROOT / 'lambdas' / name).exists():
                zip_lambda(name)
                install_deps(name)

    # Step 2: Cloud Ops
    key_id, secret = get_creds()
    env = {'AWS_ACCESS_KEY_ID': key_id, 'AWS_SECRET_ACCESS_KEY': secret}
    tf_dir = ROOT / 'terraform'

    if args.invoke:
        names = {
            'waste': 'costguard-waste-detector',
            'anomaly': 'costguard-anomaly-alerter',
            'dashboard': 'costguard-dashboard-generator'
        }
        fn = names.get(args.invoke)
        log(f'Invoking {fn}...')
        run(f'aws lambda invoke --function-name {fn} out.json && cat out.json', env=env)
        return

    run('terraform init', cwd=tf_dir, env=env)
    if args.destroy:
        run('terraform destroy -auto-approve', cwd=tf_dir, env=env)
    elif args.plan:
        run('terraform plan', cwd=tf_dir, env=env)
    else:
        run('terraform apply -auto-approve', cwd=tf_dir, env=env)
        log('Deployment complete!')

if __name__ == '__main__':
    main()
