import subprocess as _sp


def main() -> None:
    command = "git ls-remote https://github.com/SPF-OST/pytrnsys.git master".split()
    completedProcess = _sp.run(command, check=True, capture_output=True, text=True)
    longSha, _ = completedProcess.stdout.split()
    shortenedSha = longSha[0:7]
    print(shortenedSha, end="")


if __name__ == "__main__":
    main()
