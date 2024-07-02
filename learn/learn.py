#!/usr/bin/env python3
import argparse
import pickle
import random
from collections import OrderedDict


class PersistentLRUCache:
    def __init__(self, file):
        self.dic = OrderedDict()
        self.file = file
        self.load_cache()

    def recommend(self) -> str | None:
        if not self.dic:
            return None
        oldest = next(iter(self.dic))
        self.put(oldest)
        return oldest

    def random(self) -> str | None:
        if not self.dic:
            return None
        word = random.choice(list(self.dic.keys()))
        self.put(word)
        return word

    def get(self, key):
        if key in self.dic:
            return self.dic[key]
        return None

    def put(self, value):
        if value in self.dic:
            self.dic.pop(value)
        self.dic[value] = value
        self.save_cache()

    def list(self):
        return self.dic.keys()

    def save_cache(self):
        with open(self.file, "wb") as f:
            pickle.dump(self.dic, f)

    def load_cache(self):
        try:
            with open(self.file, "rb") as f:
                self.dic = pickle.load(f)
        except (FileNotFoundError, EOFError):
            self.dic = OrderedDict()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    set_parser = subparsers.add_parser("set")
    set_parser.add_argument("word", type=str)
    set_parser.add_argument("memory", type=str, default="")

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("word", type=str)

    list_parser = subparsers.add_parser("list")

    rcmd_parser = subparsers.add_parser("rcmd")
    rcmd_parser.add_argument("word", type=str)

    rand_parser = subparsers.add_parser("rand")

    args = parser.parse_args()

    cache = PersistentLRUCache("cache.pkl")

    def safe_print_word(word):
        if word is not None:
            print(f"{word}: {cache.get(word)}")
        else:
            print("No word, learn more!")

    match args.command:
        case "rcmd":
            safe_print_word(cache.recommend())
        case "rcmd":
            safe_print_word(cache.recommend())
        case "rand":
            safe_print_word(cache.random())
        case "set":
            cache.put(args.word)
        case "get":
            safe_print_word(args.word)
