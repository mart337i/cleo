from pathlib import Path
from typing import Annotated
import rich
import typer
from lxml import etree

from cleo.utils.jinja import render


def _write_template_file(file_path: Path, template_name: str, context: dict = None):
    """Helper function to write a template file"""
    if context is None:
        context = {}
    with file_path.open("w") as f:
        f.write(render(template_name=template_name, context=context))


app = typer.Typer(
    help="A series of commands/tools to assist with creating Odoo modules"
)

@app.command()
def module(
    name: Annotated[
        str, typer.Argument(help="Should be the technical name of the module")
    ],
    depends: Annotated[
        str, typer.Option(help="Dependencies, separated by comma", prompt=True)
    ],
    odoo_version: Annotated[
        float,
        typer.Option(
            help="The version of Odoo for which the module is to be created",
            prompt=True,
            envvar="ODOO_VERSION",
        ),
    ],
    controllers: Annotated[
        bool,
        typer.Option(
            help='Scaffolds the "controllers" python module with an empty file having the same name as the module'
        ),
    ] = False,
    data: Annotated[
        bool, typer.Option(help="Scaffolds an empty directory for storing data files")
    ] = False,
    models: Annotated[
        bool,
        typer.Option(
            help='Scaffolds the "models" python module with no models and also an empty security/ir.model.access.csv file, if this does not already exist'
        ),
    ] = False,
    static: Annotated[
        bool,
        typer.Option(
            help='Scaffolds the folder static content including the "src" and "description" folders'
        ),
    ] = False,
    reports: Annotated[
        bool,
        typer.Option(
            help='Scaffolds the "report" python module with no models/wizards and also an empty security/ir.model.access.csv file, if this does not already exist'
        ),
    ] = False,
    views: Annotated[
        bool, typer.Option(help="Scaffolds an empty views directory")
    ] = False,
    wizards: Annotated[
        bool,
        typer.Option(
            help='Scaffolds the "wizard" python module with no models/wizards and also an empty security/ir.model.access.csv file, if this does not already exist'
        ),
    ] = False,
    all: Annotated[
        bool,
        typer.Option(
            help="Rarely used, but this will scaffold all of the various parts in the module"
        ),
    ] = False,
    app: Annotated[
        bool,
        typer.Option(help="Scaffold the module so that it is marked as an Odoo App"),
    ] = False,
) -> None:
    """Scaffolds a new Odoo module in the current directory with the provided name

    This process will also scaffold an __manifest__.py file with sensible defaults.
    If you wish to generate a more fitting manifest file, please use odooctl make manifest, afterwards
    """
    depends: list[str] = depends.split(",")
    if all:
        controllers = True
        data = True
        models = True
        static = True
        reports = True
        views = True
        wizards = True

    root = Path(Path.cwd(), name)
    root.mkdir(parents=True)

    # Construct our manifest
    manifest = {
        "name": name,
        "version": f"{odoo_version}.1.0.0",
        "license": "OPL-1",
        "depends": depends,
        "author": "egeskov-group.dk",
        "summary": """""",
        "category": "Uncategorized",
        "description": """""",
        "data": [],
        "demo": [],
        "installable": True,
        "auto_install": False,
        "application": app,
    }

    _write_template_file(
        Path(root, "__manifest__.py"),
        "skel/module/__manifest__.py.jinja",
        {"manifest": manifest}
    )
    _write_template_file(
        Path(root, "__init__.py"),
        "skel/module/__init__.py.jinja",
        {
            "controllers": controllers,
            "data": data,
            "models": models,
            "static": static,
            "reports": reports,
            "views": views,
            "wizards": wizards,
        }
    )
    if controllers:
        controllers_dir = Path(root, "controllers")
        controllers_dir.mkdir()
        _write_template_file(
            controllers_dir / "__init__.py",
            "skel/module/controllers/__init__.py.jinja",
            {"name": name}
        )
        _write_template_file(
            controllers_dir / f"{name}.py",
            "skel/module/controllers/module.py.jinja",
            {"name": name}
        )
    if data:
        Path(root, "data").mkdir()

    if models:
        models_dir = Path(root, "models")
        models_dir.mkdir()
        _write_template_file(
            models_dir / "__init__.py",
            "skel/module/models/__init__.py.jinja"
        )
    if reports:
        reports_dir = Path(root, "report")
        reports_dir.mkdir()
        _write_template_file(
            reports_dir / "__init__.py",
            "skel/module/report/__init__.py.jinja"
        )

    if any([models, reports, wizards]):
        manifest["data"].append("security/ir.model.access.csv")
        security_dir = Path(root, "security")
        security_dir.mkdir()
        _write_template_file(
            security_dir / "ir.model.access.csv",
            "skel/module/security/ir.model.access.csv.jinja"
        )

    if static:
        Path(root, "static").mkdir()
        Path(root, "static", "src").mkdir()
        Path(root, "static", "description").mkdir()

    if views:
        Path(root, "views").mkdir()

    if wizards:
        wizard_dir = Path(root, "wizard")
        wizard_dir.mkdir()
        _write_template_file(
            wizard_dir / "__init__.py",
            "skel/module/wizard/__init__.py.jinja"
        )

    rich.print(
        f"[bold green]The module, {name}, has been scaffolded. Happy developing :)[/bold green]"
    )


@app.command()
def controller(
    module: Annotated[
        Path,
        typer.Argument(
            help="A path to the module in which we want to scaffold the controller"
        ),
    ],
    name: Annotated[
        str | None,
        typer.Argument(
            help="Should be the technical name of the controller. If omitted, the MODULE will be asumed as the name, so we usually only fill in [NAME], when we fx. want to override/extend other modules"
        ),
    ] = None,
) -> None:
    """Scaffolds a new Odoo controller in module provided, inside a subfolder called "controllers"

    This process will also update an controllers/__init__.py file with your new controller.
    """
    if not name:
        name = module
    controllers_dir = Path(module, "controllers")
    controllers_dir.mkdir(exist_ok=True)
    _write_template_file(
        controllers_dir / f"{name}.py",
        "skel/module/controllers/module.py.jinja",
        {"name": name}
    )
    with Path(module, "controllers", "__init__.py").open("a") as f:
        f.write(f"from . import {name}")

    rich.print(
        f"[bold green]The controller, {name}, has been scaffolded in module {module}. Happy developing :)[/bold green]"
    )


@app.command()
def data(
    module: Annotated[
        Path,
        typer.Argument(
            help="A path to the module in which we want to scaffold the data"
        ),
    ],
    model: Annotated[
        str, typer.Argument(help="Should be the technical name of model for the data")
    ],
) -> None:
    """Scaffolds a new Odoo data in module provided, inside a subfolder called "data"

    The process creates an empty record element in XML with basic assumed fields inside
    """
    data_dir = Path(module, "data")
    data_dir.mkdir(exist_ok=True)
    _write_template_file(
        data_dir / f'{model.replace(".", "_")}_data.xml',
        "skel/module/data/model_data.xml.jinja",
        {"model": model}
    )

    rich.print(
        f"[bold green]The data file for model, {model}, has been scaffolded in module {module}. Happy developing :)[/bold green]"
    )


@app.command()
def model(
    module: Annotated[
        Path,
        typer.Argument(
            help="A path to the module in which we want to scaffold the model"
        ),
    ],
    name: Annotated[
        str,
        typer.Argument(
            help='Should be the technical name of the model eg. "sale.order"'
        ),
    ],
    transient: Annotated[
        bool,
        typer.Option(
            help='Indicates that this will use models.TransientModel instead of models.Model. This will also place the model in "wizard" instead of "models"'
        ),
    ] = False,
    parent: Annotated[
        str,
        typer.Option(
            help='Define the parent class, which we inherit from, such as "sale.order"'
        ),
    ] = "",
    implements: Annotated[
        str,
        typer.Option(
            help='Comma-separated list of models and mixins, that we wish to implement such as "mail.thread" or "mail.activity.mixin"'
        ),
    ] = "",
) -> None:
    """Scaffolds a new Odoo model in module provided, inside a subfolder called "models"

    This process will also update an models/__init__.py file with your new model.
    This process will also update the security/ir.model.access.csv file with a basic ruleset for your new model.
    """
    if implements:
        implements: list[str] = implements.split(",")

    models_dir = Path(module, "models")
    models_dir.mkdir(exist_ok=True)
    _write_template_file(
        models_dir / f"{name}.py",
        "skel/module/models/model.py.jinja",
        {
            "name": name,
            "parent": parent or False,
            "implements": implements or [],
            "transient": transient,
        }
    )
    with Path(module, "models", "__init__.py").open("a") as f:
        f.write(f'\nfrom . import {name.replace(".", "_")}')

    # TODO: Implement a Jinja2 partial that we can call here instead. It will be better for reusability
    with Path(module, "security", "ir.model.access.csv").open("a") as f:
        f.write(
            render(
                template_name="skel/module/security/_partial/model.csv.jinja",
                context={
                    "model": name,
                    "name": module.name,
                    "group": False,
                    "read": int(True),
                    "write": int(True),
                    "create": int(True),
                    "unlink": int(True),
                },
            )
        )

    rich.print(
        f"[bold green]The model, {name}, has been scaffolded in module {module}. Happy developing :)[/bold green]"
    )


@app.command()
def view(
    module: Annotated[
        Path,
        typer.Argument(
            help="A path to the module in which we want to scaffold the views"
        ),
    ],
    model: Annotated[
        str,
        typer.Argument(
            help="Should be the technical name of the model to be used in the views"
        ),
    ],
    form: Annotated[
        bool, typer.Option(help="Setting this will generate a form view")
    ] = False,
    list: Annotated[
        bool, typer.Option(help="Setting this will generate a list view")
    ] = False,
    search: Annotated[
        bool, typer.Option(help="Setting this will generate a search view")
    ] = False,
) -> None:
    """Scaffolds a new set of views in module provided, inside a subfolder called "views"

    This process will update an existing file, if it exists, by appending the new views to the end of the file.
    For this to work the view file must have at least one <record> element
    """
    view_file = Path(
        module, "views", f'{model.replace(".", "_")}_views.xml'
    )
    if not any([form, list]):
        form = True
        list = True
        search = True
    if view_file.exists():
        # When we have an existing set of views, we need to generate the requested partial views
        # and append them to the file using lxml
        views = etree.parse(view_file)
        records = views.xpath("//record")
        if not records:
            rich.print(
                "[bold red]Malformed view file! Cannot help you update this. Aborting...[/bold red]"
            )
            typer.Exit(code=100)
        data_element = records[0].getparent()
        if form:
            data_element.append(
                etree.XML(
                    render(
                        template_name="skel/module/views/_partial/form.xml.jinja",
                        context={
                            "module": module.name,
                            "model": model,
                        },
                    )
                )
            )
        if list:
            data_element.append(
                etree.XML(
                    render(
                        template_name="skel/module/views/_partial/tree.xml.jinja",
                        context={
                            "module": module.name,
                            "model": model,
                        },
                    )
                )
            )
        if search:
            data_element.append(
                etree.XML(
                    render(
                        template_name="skel/module/views/_partial/search.xml.jinja",
                        context={
                            "module": module.name,
                            "model": model,
                        },
                    )
                )
            )

        # Finally output the data as a string that we can write
        with view_file.open("w") as f:
            xml_data = etree.tostring(
                views, encoding="UTF-8", xml_declaration=True, pretty_print=True
            )
            f.write(xml_data)

    else:
        with view_file.open("w") as f:
            f.write(
                render(
                    template_name="skel/module/views/model_views.xml.jinja",
                    context={
                        "module": module.name,
                        "model": model,
                        "form": form,
                        "list": list,
                        "search": search,
                    },
                )
            )

    rich.print(
        f"[bold green]The views in {view_file}, for model {model} have been scaffolded in module {module}. Happy developing :)[/bold green]"
    )