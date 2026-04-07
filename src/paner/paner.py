import cmd
from .utils import handle_prompt


class Paner(cmd.Cmd):
    prompt = "paner>>> "

    def do_quit(self, args):
        """
        Quit the program
        """
        return True

    do_exit = do_quit
    
    def default(self, args):
        print(args)
        return handle_prompt(args)

