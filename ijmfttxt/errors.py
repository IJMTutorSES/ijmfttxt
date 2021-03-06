from tkinter import Tk
from tkinter.messagebox import showerror


def show_error():
    Tk().withdraw()
    showerror(
        title="Internal Error",
        message="Leider ist im Modul ijmfttxt ein Fehler aufgetreten. Schicke bitte den vollständigen Traceback und dein Skript an tutor@ijm-online.de, damit der Fehler schnellstmöglich behoben werden kann. Sobald eine neue Version von ijmfttxt zur Verfügung steht, wirst du über CASS benachrichtigt. Überprüfe außerdem nochmal dein eigenes Programm, um sicherzugehen, dass der Fehler innerhalb des Moduls ijmfttxt zustande gekommen ist und nicht durch die falsche Benutzung von ijmfttxt.",
    )


class UserError(Exception):
    pass


class UserValueError(UserError):
    def __init__(self):
        super().__init__(
            "Überprüfe welche Werte übergeben werden müssen! Weitere Infos findest du im Errorsheet (3.0.6) unter ValueError. (Dies ist ein Fehler, der in deinem Skript entstanden ist!)"
        )


class UserTypeError(UserError):
    def __init__(self):
        super().__init__(
            "Überprüfe welcher Typ erwartet wird! Weiter Infos findest du im Errorsheet (3.0.6) unter TypeError. (Dies ist ein Fehler, der in deinem Skript entstanden ist!)"
        )


def type_checker(t_args=None, t_kwargs=None):
    def check_value(arg, v_arg):
        if v_arg == "FLOAT":
            try:
                float(arg)
            except ValueError:
                raise UserValueError
        elif v_arg == "INTEGER":
            try:
                int(arg)
            except ValueError:
                raise UserValueError

    def wrapper(func):
        def decorator(*args, **kwargs):
            if t_args:
                for i, arg in enumerate(args[len(args) - len(t_args) :]):
                    if not isinstance(t := t_args[i], str):
                        if not isinstance(arg, t):
                            raise UserTypeError()
                    else:
                        check_value(arg, t)
            if t_kwargs:
                for key, kwarg in kwargs.items():
                    if not isinstance(t := t_kwargs[key], str):
                        if not isinstance(kwarg, t):
                            raise UserTypeError()
                    else:
                        check_value(kwarg, t)
            return func(*args, **kwargs)

        return decorator

    return wrapper


def error_handler(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if not isinstance(e, UserError):
                show_error()
            raise e

    return inner


if __name__ == "__main__":
    show_error()
