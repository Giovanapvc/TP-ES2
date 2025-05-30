import repo, service
from entities import GENRES, Artist, Song

CANCEL_KEY = "F"

def pause():
    input("\nPressione Enter para continuar…")

def choose(prompt: str, options: dict):
    while True:
        print(prompt)
        for key, desc in options.items():
            print(f"  [{key}] {desc}")
        print(f"(ou pressione '{CANCEL_KEY}' + ENTER para cancelar)")
        choice = input("> ").strip().upper()
        if choice == CANCEL_KEY:
            return CANCEL_KEY
        if choice in options:
            return choice
        print("Opção inválida.\n")

def inp(prompt: str):
    val = input(f"{prompt} (ou '{CANCEL_KEY}' p/ cancelar): ").strip()
    return None if val.upper() == CANCEL_KEY else val

# ---------------- Main -----------------
def main():
    store = repo.load()
    while True:
        choice = choose("Menu principal", {"A":"Sou artista","U":"Sou usuário","Q":"Sair"})
        if choice in ("Q", CANCEL_KEY):
            break
        if choice=="A": artist_flow(store)
        else: user_flow(store)

# --------------- Artist Flow ---------------
def artist_flow(store):
    sub = choose("Como artista…", {"N":"Criar perfil","L":"Login","B":"Voltar"})
    if sub in ("B", CANCEL_KEY): return
    if sub=="N":
        while True:
            name = inp("Nome artístico único")
            if name is None: return
            try:
                artist = service.add_artist(store, name, bio=inp("Bio"))
                print(f"✔ Perfil criado! Bem-vindo, {artist.name}.\n"); pause(); break
            except ValueError:
                print("Nome já existe.\n")
        return
    while True:
        name = inp("Digite seu nome artístico")
        if name is None: return
        artist = service.find_artist_by_name(store, name)
        if artist: break
        print("Nome não encontrado.\n")
    artist_dashboard(store, artist)

def artist_dashboard(store, artist: Artist):
    while True:
        act = choose(f"Artista {artist.name}", {"S":"Add música","E":"Editar música","V":"Stats","B":"Voltar"})
        if act in ("B", CANCEL_KEY): break
        if act=="S":
            title=inp("Título"); 
            if title is None: continue
            desc=inp("Descrição"); 
            if desc is None: continue
            genre=choose("Gênero",{g.upper():g for g in GENRES})
            if genre in (CANCEL_KEY, None): continue
            link=inp("Link"); 
            if link is None: continue
            fp=inp("File path")
            service.add_song(store, artist.id,title=title,description=desc,genre=genre,link=link,file_path=fp or "")
            print("✔ Música adicionada.\n"); pause()
        elif act=="E":
            if not artist.songs: print("Sem músicas.\n"); pause(); continue
            song=select_song(artist.songs)
            if song: edit_song(store, artist, song)
        elif act=="V":
            stats_menu(store, artist)

def stats_menu(store, artist):
    while True:
        print(f"Likes: {artist.likes}")
        for idx,s in enumerate(artist.songs,1):
            print(f"{idx}. {s.title} [{s.genre}] {s.likes} likes ({len(s.opinions)} op.)")
        act=choose("Stats opções", {"O":"Ver opiniões de música","B":"Voltar"})
        if act in ("B", CANCEL_KEY): break
        if act=="O":
            song=select_song(artist.songs)
            if not song: continue
            if song.opinions:
                print("\nOpiniões:")
                for op in song.opinions: print(f"- {op}")
            else:
                print("Nenhuma opinião ainda.")
            pause()

def select_song(songs):
    for i,s in enumerate(songs,1):
        print(f"{i}. {s.title} ({s.genre})")
    val=inp("Número")
    if val is None: return None
    try: n=int(val)-1
    except ValueError: return None
    return songs[n] if 0<=n<len(songs) else None

def edit_song(store, artist, song):
    while True:
        act=choose(f"Editar {song.title}",{"T":"Título","D":"Descrição","G":"Gênero","B":"Voltar"})
        if act in ("B", CANCEL_KEY): break
        if act=="T":
            new=inp("Novo título"); 
            if new is not None: service.edit_song(store,artist.id,song.id,title=new)
        elif act=="D":
            new=inp("Nova descrição"); 
            if new is not None: service.edit_song(store,artist.id,song.id,description=new)
        elif act=="G":
            g=choose("Gênero",{g.upper():g for g in GENRES})
            if g not in (CANCEL_KEY, None): service.edit_song(store,artist.id,song.id,genre=g)
        print("Atualizado.\n")

# --------------- User Flow ---------------
def user_flow(store):
    liked=set()
    while True:
        act=choose("Usuário",{
            "G":"Buscar por gênero",
            "L":"Minhas curtidas",
            "A":"Artistas + curtir",
            "O":"Opinar por nome",
            "B":"Voltar"})
        if act in ("B", CANCEL_KEY): break
        if act=="G":
            genre=choose("Gênero",{g.upper():g for g in GENRES})
            if genre in (CANCEL_KEY,None): continue
            browse_songs(service.songs_by_genre_sorted(store,genre),liked,store)
        elif act=="L":
            browse_songs([s for a in store.values() for s in a.songs if s.id in liked],liked,store)
        elif act=="A":
            artists=service.artists_sorted(store)
            for i,a in enumerate(artists,1): print(f"{i}. {a.name} ({a.likes})")
            val=inp("Número para curtir")
            if val is None or not val.isdigit(): continue
            n=int(val); 
            if 1<=n<=len(artists):
                service.like_artist(store,artists[n-1].id); print("Curtido.\n"); pause()
        elif act=="O":
            while True:
                name=inp("Nome da música")
                if name is None: break
                song=service.find_song_by_name(store,name)
                if song: 
                    show_song(song,store); opinion_flow(store,song,liked); break
                print("Não encontrada.\n")

def browse_songs(song_list, liked, store):
    if not song_list: print("Nenhuma.\n"); pause(); return
    song=select_song(song_list)
    if song: show_song(song,store); song_menu(store,song,liked)

def show_song(song,store):
    art=[a for a in store.values() if song in a.songs][0]
    print(f"\n{song.title} – {art.name}\n{song.description}\nLikes:{song.likes}\nLink:{song.link}\n")

def song_menu(store,song,liked):
    art=[a for a in store.values() if song in a.songs][0]
    while True:
        act=choose("Opções",{"C":"Curtir","O":"Opinar","B":"Voltar"})
        if act in ("B", CANCEL_KEY): break
        if act=="C":
            if song.id not in liked:
                service.like_song(store,art.id,song.id); liked.add(song.id); print("Curtido.\n")
            else: print("Já curtiu.\n")
        elif act=="O": opinion_flow(store,song,liked)

def opinion_flow(store,song,liked):
    art=[a for a in store.values() if song in a.songs][0]
    txt=inp("Opinião")
    if txt is None: return
    service.add_opinion(store,art.id,song.id,txt)
    if song.id not in liked:
        service.like_song(store,art.id,song.id); liked.add(song.id)
    print("Opinião + like salvos.\n"); pause()

if __name__=="__main__":
    main()