import os, json, subprocess
path = r"C:\Users\prabh\.taxos-gh-token"
token = open(path, "r", encoding="utf-8").read().strip()
print("TOKEN_LOADED", len(token))
