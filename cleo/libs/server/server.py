import shlex
from invoke import run, UnexpectedExit

def restart(username, domain_name, service):
    # Sanitize inputs
    username = shlex.quote(username)
    domain_name = shlex.quote(domain_name)
    service = shlex.quote(service)

    # Construct safe SSH command
    cmd = f"ssh {username}@{domain_name} 'sudo systemctl restart {service}'"

    print(f"Executing restart: {cmd}")
    
    try:
        result = run(cmd, hide=False, warn=True)
        if result.ok:
            print(f"✅ Successfully restarted {service} on {domain_name}")
        else:
            print(f"⚠️ Failed to restart {service}. Exit code: {result.exited}")
    except UnexpectedExit as e:
        print(f"❌ Command failed: {e.result.stderr}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
