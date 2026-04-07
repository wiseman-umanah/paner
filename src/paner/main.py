from pyfiglet import Figlet
from rich import print as rprint
from rich.console import Console
from importlib.metadata import version
import os
from .paner import Paner
from .config import (get_api_key, save_api_key)
import getpass


def main():
    console = Console()

    os.system('cls' if  os.name == 'nt' else 'clear')

    # Welcome message for user
    f = Figlet(font='dos_rebel')
    console.print(f.renderText("PANER"), style="green")
    rprint(f"Terminal PDF analyzer - [bold green]{version('paner')}[/bold green]")


    # Handle api key
    api_key = None
    while api_key is None:
        try:
            api_key = get_api_key()
            rprint("[bold green]API Key loaded successfully!!![/bold green], Drop your pdf path")
        except Exception as error:
            console.print(str(error), style="red")
            try:
                new_api_key = getpass.getpass(prompt=f"Enter your Groq API Key: \t", echo_char="*")
                save_api_key(new_api_key)
                api_key = new_api_key
            except ValueError as error:
                console.print(str(error), style="bold red")

    Paner().cmdloop()


