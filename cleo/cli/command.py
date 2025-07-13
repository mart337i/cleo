# Standard library imports
from importlib import import_module
from pathlib import Path

# Third-party imports
import rich
import typer

# Local imports
from cleo.config import configuration

cli = typer.Typer(help="cleo CLI application")

def discover_commands(commands_dir: Path):
    """Discover and register commands from CLI directories"""
    if not commands_dir.exists():
        rich.print(f"[red]Command directory not found at {commands_dir}[/red]")
        return
    
    module_apps = {}
    
    # Scan for Python files in commands directory structure
    for item in commands_dir.rglob("*.py"):
        if item.name == '__init__.py':
            continue
            
        relative_path = item.relative_to(commands_dir)
        parts = relative_path.parts
        
        try:
            import_path = _build_import_path(commands_dir, item)
            module_name = item.stem
            module = import_module(import_path)
            
            if not (hasattr(module, 'app') and isinstance(module.app, typer.Typer)):
                if configuration.debug:
                    rich.print(f"[yellow]Module {import_path} does not contain a typer app[/yellow]")
                continue
            
            if len(parts) == 1:
                # Direct file in commands directory - add directly to main CLI
                cli.add_typer(module.app, name=module_name)
                if configuration.debug:
                    rich.print(f"[green]Registered top-level command: {module_name}[/green]")
            else:
                # File in subdirectory - group under parent module
                parent_module = parts[0]
                
                if parent_module not in module_apps:
                    module_apps[parent_module] = typer.Typer(
                        name=parent_module, 
                        help=f"Commands for {parent_module}"
                    )
                
                _register_typer_app(module, module_name, parent_module, module_apps)
                
        except ImportError as e:
            _log_error(f"Failed to import module {import_path}", e)
        except Exception as e:
            _log_error(f"Error processing {item}", e)
    
    # Add all module apps to the main CLI
    for module_app in module_apps.values():
        cli.add_typer(module_app)


def _build_import_path(commands_dir: Path, item: Path) -> str:
    """Build the correct import path for a module in the commands directory."""
    relative_path = item.relative_to(commands_dir)
    parts = list(relative_path.parts)
    parts[-1] = parts[-1].replace('.py', '')
    return "commands." + ".".join(parts)


def _register_typer_app(module, module_name, parent_module, module_apps):
    """Register a Typer app with its parent module."""
    cmd_name = getattr(module, 'name', module_name)
    module_apps[parent_module].add_typer(module.app, name=cmd_name)
    
    if hasattr(module, '__doc__') and module.__doc__:
        module.app.info.help = module.__doc__.strip()
    
    if configuration.debug:
        rich.print(f"[green]Registered command: {parent_module} {cmd_name}[/green]")


def _log_error(message: str, error: Exception):
    """Log an error message if debug is enabled."""
    if configuration.debug:
        rich.print(f"[red]{message}: {error}[/red]")

@cli.command(help="Generate a config file with environment variables")
def generate(output_path: str = typer.Option("cleo.conf", help="Path to output the config file")):
    """Generate a configuration file with default environment variables."""
    configuration.create_config(output_path)


@cli.command(help="Show the current CLI version.")
def version():
    """Show the current version."""
    from cleo import VERSION
    rich.print(f"[bold]Version:[/bold] {VERSION}")

@cli.command(help="Get loaded ENV")
def get_env():
    rich.print(configuration.env)

@cli.command(help="Get loaded config")
def get_config():
    rich.print(configuration.loaded_config)

def main():
    """Main entry point for the CLI"""
    commands_dir = Path(__file__).parent.parent.parent / "commands"
    discover_commands(commands_dir)
    cli()