# Standard library imports
from importlib import import_module
from pathlib import Path

# Third-party imports
import rich
import typer

# Local imports
from cleo.config import configuration
from cleo import addons

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
            
        # Determine the module structure
        relative_path = item.relative_to(commands_dir)
        parts = relative_path.parts
        
        if len(parts) == 1:
            # Direct file in commands directory (e.g., repo.py)
            parent_module = item.stem
        else:
            # File in subdirectory (e.g., instance/dev.py)
            parent_module = parts[0]
        
        # Create a new Typer app for this module if it doesn't exist
        if parent_module not in module_apps:
            module_apps[parent_module] = typer.Typer(
                name=parent_module, 
                help=f"Commands for {parent_module}"
            )
        
        try:
            # Build import path
            import_path = _build_import_path_new(commands_dir, item)
            module_name = item.stem
            
            # Import the module
            module = import_module(import_path)
            
            # Register the Typer app if available
            if hasattr(module, 'app') and isinstance(module.app, typer.Typer):
                _register_typer_app(module, module_name, parent_module, module_apps, import_path)
            elif configuration.debug:
                rich.print(f"[yellow]Module {import_path} does not contain a typer app[/yellow]")
                
        except ImportError as e:
            _log_error(f"Failed to import module {import_path}", e)
        except Exception as e:
            _log_error(f"Error processing {item}", e)
    
    # Add all module apps to the main CLI
    for module_name, module_app in module_apps.items():
        cli.add_typer(module_app)


def _build_import_path(cli_dir: Path, item: Path) -> str:
    """Build the correct import path for a module."""
    parts = list(cli_dir.parts)
    module_name = item.name.replace('.py', '')
    
    if "addons" in parts:
        addons_index = parts.index("addons")
        module_parts = parts[addons_index:]
        return ".".join(module_parts + [module_name])
    else:
        return f"cli.{module_name}"


def _build_import_path_new(commands_dir: Path, item: Path) -> str:
    """Build the correct import path for a module in the commands directory."""
    relative_path = item.relative_to(commands_dir)
    parts = list(relative_path.parts)
    
    # Remove the .py extension from the last part
    parts[-1] = parts[-1].replace('.py', '')
    
    # Build the import path
    return "commands." + ".".join(parts)


def _register_typer_app(module, module_name, parent_module, module_apps, import_path):
    """Register a Typer app with its parent module."""
    cmd_name = getattr(module, 'name', module_name)
    module_apps[parent_module].add_typer(module.app, name=cmd_name)
    
    # Add doc string as help if available
    if hasattr(module, '__doc__') and module.__doc__:
        module.app.info.help = module.__doc__.strip()
    
    if configuration.debug:
        rich.print(f"[green]Registered command: {parent_module} {cmd_name} from {import_path}[/green]")


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
    discover_commands(addons)
    cli()