import os
import sys
import json

def _main():
    pass


def _procedures():
    pass

def read_json(path):
    with open(path, 'r', encoding='utf8') as f:
        data = f.read()
        data = json.loads(data)
    return data

def save_json(data, path, sort=False):
    with open(path, 'w', encoding='utf8') as f:
        f.write(json.dumps(data, indent=4, sort_keys=sort, ensure_ascii=False))

def print_json(data):
    print(json.dumps(data,indent=4,ensure_ascii=False))


if __name__ == '__main__':
    _main()
