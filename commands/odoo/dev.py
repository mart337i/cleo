
import base64
import os
from typing import Annotated

import invoke
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from cleo.utils.decorators.exception import disable_traceback
from cleo import utils
from cleo.libs.server.server import restart as service_restart

app = typer.Typer(help="A set of commands to interact with Moduels on a given instance")
console = Console()

@app.command(help="Deploy one or more odoo modules to a given instance")
@disable_traceback
def deploy(
    user: Annotated[str, typer.Option()] = "",
    server: Annotated[str, typer.Option()] = "",
    database: Annotated[str, typer.Option()] = "",
    remote: Annotated[str, typer.Option()] = "~/src/custom",
    modules: Annotated[str, typer.Argument(help="Module path(s) or 'all' to deploy all modules in current directory")] = None,
    verbose: Annotated[bool, typer.Option()] = False,
    force: Annotated[bool, typer.Option(hidden=True)] = False,
) -> None:

    if not any(keyword in server for keyword in ["test", "dev", "dev2", "upgrade"]) and force == False:
        raise ValueError("Nope, not allowed")

    if not database:
        database = user

    # Handle module paths
    module_paths = []
    if modules.lower() == "all":
        # Find all directories in current directory that contain __manifest__.py
        current_dir = os.getcwd()
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "__manifest__.py")):
                module_paths.append(item_path)
        
        if not module_paths:
            console.print("[red]No Odoo modules found in current directory[/red]")
            return
            
        console.print(f"[blue]Found {len(module_paths)} modules to deploy:[/blue]")
        for path in module_paths:
            console.print(f"  - {os.path.basename(path)}")
    else:
        # Split comma-separated paths and clean them
        module_paths = [path.strip() for path in modules.split(",")]
        
        # Validate all paths exist
        for path in module_paths:
            if not os.path.exists(path):
                console.print(f"[red]Module path does not exist: {path}[/red]")
                return
            if not os.path.exists(os.path.join(path, "__manifest__.py")):
                console.print(f"[red]Not a valid Odoo module (no __manifest__.py): {path}[/red]")
                return

    with Progress(
        SpinnerColumn(), TextColumn("[blue]{task.description}"), transient=True
    ) as progress:
        for module_path in module_paths:
            module_name = os.path.basename(module_path)
            transfer_task = progress.add_task(
                description=f"[blue]Transferring module {module_name} to {server}..."
            )

            # Create directory on remote server
            mkdir_cmd = f'ssh {user}@{server} "mkdir -p {remote}/{module_name}"'
            invoke.run(command=mkdir_cmd, hide=verbose)

            # Copy module files
            scp_cmd = f"scp -r {module_path}/* {user}@{server}:{remote}/{module_name}/"
            invoke.run(command=scp_cmd, hide=verbose)

            progress.update(transfer_task, completed=True)

    console.print(
        f"[bold blue]:heavy_check_mark:  All modules transferred successfully![/bold blue]"
    )

    # Restart instance
    service_restart(username=user, domain_name=server, service=f"{database}.service")

    # Install/update all modules
    module_names = [os.path.basename(path) for path in module_paths]
    
    # Create the Odoo shell script for multiple modules
    odoo_bin_shell_template = """
import importlib
import sys
import os
# Add the custom directory to the Python path
custom_path = os.path.expanduser("{{ remote_path }}")
if custom_path not in sys.path:
    sys.path.insert(0, custom_path)

# Update module list first
env['ir.module.module'].update_list()

# Process each module
module_names = {{ module_names }}
for module_name in module_names:
    print(f"Processing module: {module_name}")
    module = env['ir.module.module'].search([('name', '=', module_name)], limit=1)
    if module:
        if module.state == 'installed':
            print(f"Module {module_name} is already installed. Upgrading...")
            module.button_immediate_upgrade()
        else:
            print(f"Installing module {module_name}...")
            module.button_immediate_install()
        print(f"Module {module_name} has been successfully {'upgraded' if module.state == 'installed' else 'installed'}")
    else:
        print(f"Module {module_name} not found. Please check the module name.")
    print("-" * 50)

env.cr.commit()
print(f"All modules processed successfully!")
"""
    
    process_code = utils.templates.render_from_string(
        template_str=odoo_bin_shell_template,
        context={"module_names": module_names, "remote_path": remote},
    )
    process_code_b64 = base64.b64encode(process_code.encode()).decode()

    with Progress(
        SpinnerColumn(), TextColumn("[blue]{task.description}"), transient=True
    ) as progress:
        # Execute the installation command
        cmd = (
            f'ssh {user}@{server} "source bin/activate && '
            f"echo '{process_code_b64}' | base64 -d | "
            f'src/odoo/odoo-bin shell -c .config/odoo/odoo.conf -d {database} --no-http  --log-level=warn"'
        )
        installing = progress.add_task(f"[blue] Installing/updating modules...")
        invoke.run(command=cmd)
        progress.update(installing, completed=True)
    console.print(
        f"[bold blue]:heavy_check_mark:  Installed/updated successfully![/bold blue]"
    )

    if len(module_names) == 1:
        console.print(
            f"[bold blue]:heavy_check_mark:  Module {module_names[0]} deployed successfully on {user}@{server}![/bold blue]"
        )
    else:
        console.print(
            f"[bold blue]:heavy_check_mark:  {len(module_names)} modules deployed successfully on {user}@{server}![/bold blue]"
        )
        console.print("[blue]Deployed modules:[/blue]")
        for module_name in module_names:
            console.print(f"  - {module_name}")


@app.command(help="Simple live logs with search")
@disable_traceback
def logs(
    user: Annotated[str, typer.Option()] = "",
    server: Annotated[str, typer.Option()] = "",
    database: Annotated[str, typer.Option()] = "",
    remote: Annotated[str, typer.Option()] = "logs/odoo.log",
    search: Annotated[str, typer.Option(help="Filter logs by a search term (optional)")] = "",
) -> None:
    if not database:
        database = user
   
    if search:
        cmd = f"ssh {user}@{server} 'tail -f /home/{user}/{remote}' | grep --line-buffered --color=always -i '{search}'"
    else:
        cmd = f"ssh {user}@{server} 'tail -f /home/{user}/{remote}'"
   
    console.print(f"[bold green]Streaming logs from {user}@{server}:{remote}[/bold green]")
    if search:
        console.print(f"[bold yellow]Filtering for: {search}[/bold yellow]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")
   
    try:
        invoke.run(cmd, pty=True, warn=True)
    except KeyboardInterrupt:
        console.print("\n[bold red]Stopped log streaming[/bold red]")
    except invoke.exceptions.UnexpectedExit as e:
        # Handle SSH connection termination gracefully
        if e.result.exited == 255:
            console.print("\n[bold red]Stopped log streaming[/bold red]")
        else:
            # Re-raise for other unexpected exit codes
            raise
