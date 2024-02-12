import importlib.metadata as _imeta

import packaging.version as _pver


def main() -> None:
    serializedVersion = _imeta.version("pytrnsys")
    version = _pver.parse(serializedVersion)
    localPart = version.local
    assert localPart
    sha = localPart.rsplit(".", maxsplit=1)[-1]
    shortenedSha = sha[0:7]
    print(shortenedSha)


if __name__ == "__main__":
    main()
