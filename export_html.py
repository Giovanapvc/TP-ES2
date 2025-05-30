import repo, html
from pathlib import Path
def render():
    store=repo.load()
    out=["<html><meta charset='utf-8'><body><h1>Export</h1>"]
    for a in store.values():
        out.append(f"<h2>{html.escape(a.name)} ({a.likes})</h2><p>{html.escape(a.bio)}</p>")
        for s in a.songs:
            out.append(f"<h3>{html.escape(s.title)} [{s.genre}] {s.likes}</h3>")
            out.append(f"<p>{html.escape(s.description)}</p>")
    Path("export.html").write_text('\n'.join(out))
    print("export.html gerado.")
if __name__=='__main__': render()