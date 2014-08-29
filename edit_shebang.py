#!/usr/bin/env python2

import sys

def process(fn):
    with open(fn, "r") as f:
        data = f.read()

    data = data.replace("/usr/bin/env python", "/usr/bin/env python2")

    with open(fn, "w") as f:
        f.write(data)


def main():
    for i in sys.argv[1:]:
        process(i)

if __name__ == "__main__":
    main()
