import subprocess as _sp
import sys as _sys


def main() -> None:
    if len(_sys.argv) != 3:
        print(f"ERROR: Usage: {_sys.argv[0]} <repo url> <git ref>")
        _sys.exit(-1)

    url = _sys.argv[1]
    gitRef = _sys.argv[2]

    command = f"git ls-remote {url} {gitRef}".split()
    completedProcess = _sp.run(
        command, check=True, capture_output=True, text=True
    )
    longSha, _ = completedProcess.stdout.split()
    shortenedSha = longSha[0:7]
    print(shortenedSha, end="")


if __name__ == "__main__":
    main()
