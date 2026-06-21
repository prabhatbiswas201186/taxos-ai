import pathlib, json

OUT  = pathlib.Path(r'C:/Users/prabh/taxos-ai/index.html')
BODY = pathlib.Path(r'C:/Users/prabh/taxos-ai/_body.py')

# Clean any previous artifacts. Remove custom <div id="app"></div> we want to keep it.
print(OUT.read_text(encoding='utf-8', errors='ignore')[:80])
