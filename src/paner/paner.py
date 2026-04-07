import cmd
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from .utils import (
    handle_prompt,
    list_documents,
    select_document,
    get_active_document_name,
)


class Paner(cmd.Cmd):
    prompt = "paner>>> "

    def __init__(self):
        super().__init__()
        self.console = Console()
        self._update_prompt()

    def _update_prompt(self):
        """
        Refresh the CLI prompt with the active document name.
        """
        name = get_active_document_name()
        if name:
            self.prompt = f"paner[{name}]>>> "
        else:
            self.prompt = "paner>>> "

    def _print_response(self, response: str):
        """
        Render assistant responses with Markdown formatting and a blank line.
        """
        if not response:
            return
        try:
            self.console.print(Markdown(response), soft_wrap=True)
        except Exception:
            self.console.print(response, soft_wrap=True)
        self.console.print()

    def do_quit(self, args):
        """
        Quit the program
        """
        return True

    do_exit = do_quit

    def do_list(self, args):
        """
        List all PDFs indexed in the current session.
        """
        docs = list_documents()
        if not docs:
            self.console.print("[yellow]No PDFs loaded yet.[/yellow]")
            return False

        table = Table(title="Loaded PDFs")
        table.add_column("#", justify="right")
        table.add_column("Name")
        table.add_column("Path")
        table.add_column("Active")

        for doc in docs:
            table.add_row(
                str(doc["index"]),
                doc["name"],
                doc["path"],
                "✅" if doc["is_active"] else "",
            )

        self.console.print(table)
        return False

    def do_use(self, args):
        """
        Focus questions on a specific PDF: `use 1`, `use report.pdf`, or `use all`.
        """
        success, message = select_document(args)
        style = "green" if success else "red"
        self.console.print(f"[{style}]{message}[/{style}]")
        self._update_prompt()
        return False

    def emptyline(self):
        """
        Prevent repeating the last command on empty input.
        """
        return False
    
    def default(self, args):
        """
        Prompt handler for all logic and prompting 
        """
        text = args.strip()
        if not text:
            return False

        response = handle_prompt(text)
        self._print_response(response)
        self._update_prompt()
        return False
