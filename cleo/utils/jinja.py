from pathlib import Path
from typing import Dict, Any, Optional, Union, List

from jinja2 import (
    Environment, 
    FileSystemLoader, 
    Template, 
    TemplateError, 
    select_autoescape,
    ChoiceLoader
)

from cleo import addons,templates_dir

def _setup_jinja_environment():
    def discover_template_dirs() -> List[Path]:
        addon_template_dirs = []
        
        if addons.exists() and addons.is_dir():
            for addon_dir in addons.iterdir():
                if addon_dir.is_dir():
                    # Check if this addon has a templates directory
                    addon_templates_path = addon_dir / 'templates'
                    if addon_templates_path.exists() and addon_templates_path.is_dir():
                        addon_template_dirs.append(addon_templates_path)
        
        return addon_template_dirs
    
    addons_temp = discover_template_dirs() + [templates_dir]

    loaders = [FileSystemLoader(path.absolute()) for path in addons_temp]

    env = Environment(
        loader=ChoiceLoader(loaders),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )
    
    return env

def render(template_name: str, context: Optional[Dict[str, Any]] = {}) -> str:
    """
    Render a template from the filesystem.
    """
    try:
        template = _env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        raise TemplateError(f"Failed to render template '{template_name}': {str(e)}") from e

def render_from_string(template_str: str, context: Optional[Dict[str, Any]] = {}) -> str:
    """
    Render a template from a string.
    """
    try:
        template = Environment().from_string(template_str)
        return template.render(**context)
    except Exception as e:
        raise TemplateError(f"Failed to render template string: {str(e)}") from e

def load_template(template_name: str) -> Template:
    try:
        return _env.get_template(template_name)
    except Exception as e:
        raise TemplateError(f"Failed to load template '{template_name}': {str(e)}") from e

def get_environment() -> Environment:
    return _env

def set_environment(environment : Environment) -> Environment:
    global _env
    _env = environment
    return _env

_env = _setup_jinja_environment()
