import sys

__all__ = ["askToContinue", "tofloat"]


def askToContinue():
    response = input("Do you want to continue ?")
    print(response)
    if 'n' in response:
        sys.exit('aborted')


def tofloat(string):
    import re

    if string.isdigit(): return float(string)

    matchreg = r"^([0-9]+)[.]([0-9]+)"
    match = re.match(matchreg, string)
    if match:
        return float(match.group(0))

    matchreg = r"^([0-9]+)[/]([0-9]+)"
    match = re.match(matchreg, string)
    if match:
        print(match)
        nominator = float(match.group(1))
        denominator = float(match.group(2))
        return nominator / denominator
