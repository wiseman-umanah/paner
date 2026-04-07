from pyfiglet import Figlet
from rich import print as rprint
from rich.console import Console
from importlib.metadata import version
import os

console = Console()

os.system('cls' if  os.name == 'nt' else 'clear')

f = Figlet(font='dos_rebel')
console.print(f.renderText("PANER"), style="green")
rprint(f"Terminal PDF analyzer - [bold green]{version('paner')}[/bold green]")

