import invoke

def restart(username,domain_name,service):
    cmd = f"ssh {username}@{domain_name} 'sudo systemctl restart {service}'"
    invoke.run(cmd)