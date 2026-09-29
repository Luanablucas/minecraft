
import random
import secrets
import sqlite3
from collections import deque
from pathlib import Path


BANCO = Path(__file__).resolve().parent / "masmorras.db"
TEMAS = {
    "Biblioteca amaldiçoada": {
        "salas": ["Arquivo proibido", "Sala dos escribas", "Galeria dos tomos"],
        "inimigo": "esqueleto bibliotecário",
        "tesouro": "livro de encantamentos",
        "historia": "Um livro roubado condenou os guardiões a vigiar estas estantes para sempre.",
    },
    "Mina abandonada": {
        "salas": ["Poço seco", "Depósito de ferramentas", "Galeria de cristais"],
        "inimigo": "aranha das cavernas",
        "tesouro": "diamante antigo",
        "historia": "Os mineiros desapareceram depois de ouvir batidas do outro lado da rocha.",
    },
    "Cripta congelada": {
        "salas": ["Câmara de gelo", "Salão dos ancestrais", "Altar esquecido"],
        "inimigo": "guardião congelado",
        "tesouro": "coroa de gelo",
        "historia": "Uma coroa mantém o inverno preso nas paredes desta cripta.",
    },
}
DIRECOES = [(0, -1), (1, 0), (0, 1), (-1, 0)]


def criar_banco(conexao):
    """Uma masmorra possui várias salas e várias conexões entre elas."""
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.executescript("""
        CREATE TABLE IF NOT EXISTS masmorras (
            id INTEGER PRIMARY KEY,
            tema TEXT NOT NULL,
            semente TEXT NOT NULL,
            dificuldade TEXT NOT NULL,
            historia TEXT NOT NULL,
            criada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS salas (
            masmorra_id INTEGER NOT NULL REFERENCES masmorras(id),
            numero INTEGER NOT NULL,
            nome TEXT NOT NULL,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            evento TEXT NOT NULL,
            PRIMARY KEY (masmorra_id, numero),
            UNIQUE (masmorra_id, x, y)
        );
        CREATE TABLE IF NOT EXISTS conexoes (
            masmorra_id INTEGER NOT NULL,
            origem INTEGER NOT NULL,
            destino INTEGER NOT NULL,
            PRIMARY KEY (masmorra_id, origem, destino),
            FOREIGN KEY (masmorra_id, origem) REFERENCES salas(masmorra_id, numero),
            FOREIGN KEY (masmorra_id, destino) REFERENCES salas(masmorra_id, numero)
        );
    """)


def gerar_masmorra(tema, semente, dificuldade="Normal"):
    """Cada sala nova se conecta a uma existente: nenhuma fica isolada."""
    rng = random.Random(semente)
    catalogo = TEMAS[tema]
    salas = [{"numero": 1, "nome": "Entrada", "x": 0, "y": 0, "evento": "Uma porta se fecha atrás de você."}]
    conexoes = []
    ocupadas = {(0, 0)}
    for numero in range(2, 6):
        opcoes = []
        for sala in salas:
            for dx, dy in DIRECOES:
                x, y = sala["x"] + dx, sala["y"] + dy
                if (x, y) not in ocupadas:
                    opcoes.append((sala["numero"], x, y))
        origem, x, y = rng.choice(opcoes)
        ocupadas.add((x, y))
        salas.append({"numero": numero, "nome": "", "x": x, "y": y, "evento": ""})
        conexoes.append((origem, numero))

    # Busca em largura -- encontra a sala mais distante
    distancias = {1: 0}
    fila = deque([1])
    while fila:
        atual = fila.popleft()
        for vizinho in vizinhos(atual, conexoes):
            if vizinho not in distancias:
                distancias[vizinho] = distancias[atual] + 1
                fila.append(vizinho)
    saida = max(distancias, key=distancias.get)
    interiores = [s for s in salas if s["numero"] not in (1, saida)]
    rng.shuffle(interiores)
    nomes = rng.sample(catalogo["salas"], len(interiores))
    quantidade = {"Tranquila": 1, "Normal": 2, "Perigosa": 4}[dificuldade]
    eventos = [
        f"Tesouro encontrado: {catalogo['tesouro']}!",
        f"Você avista {quantidade} criatura(s): {catalogo['inimigo']}. Passe com cuidado!",
        "Armadilha! Uma placa no chão dispara flechas contra a parede.",
    ]
    for sala, nome, evento in zip(interiores, nomes, eventos):
        sala.update(nome=nome, evento=evento)
    salas[saida - 1].update(nome="Saída", evento="Uma escadaria leva de volta à superfície.")
    return {"tema": tema, "semente": semente, "dificuldade": dificuldade,
            "historia": catalogo["historia"], "salas": salas, "conexoes": conexoes}


def vizinhos(numero, conexoes):
    resultado = []
    for origem, destino in conexoes:
        if origem == numero:
            resultado.append(destino)
        elif destino == numero:
            resultado.append(origem)
    return sorted(resultado)


def salvar_masmorra(conexao, masmorra):
    # A transação salva tudo junto; um erro desfaz a operação inteira.
    with conexao:
        cursor = conexao.execute(
            "INSERT INTO masmorras (tema, semente, dificuldade, historia) VALUES (?, ?, ?, ?)",
            (masmorra["tema"], masmorra["semente"], masmorra["dificuldade"], masmorra["historia"]),
        )
        identificador = cursor.lastrowid
        conexao.executemany("INSERT INTO salas VALUES (?, ?, ?, ?, ?, ?)", [
            (identificador, s["numero"], s["nome"], s["x"], s["y"], s["evento"])
            for s in masmorra["salas"]
        ])
        conexao.executemany("INSERT INTO conexoes VALUES (?, ?, ?)", [
            (identificador, origem, destino) for origem, destino in masmorra["conexoes"]
        ])
    return identificador


def carregar_masmorra(conexao, identificador):
    registro = conexao.execute("SELECT * FROM masmorras WHERE id = ?", (identificador,)).fetchone()
    if registro is None:
        return None
    masmorra = dict(registro)
    masmorra["salas"] = [dict(s) for s in conexao.execute(
        "SELECT * FROM salas WHERE masmorra_id = ? ORDER BY numero", (identificador,))]
    masmorra["conexoes"] = [tuple(c) for c in conexao.execute(
        "SELECT origem, destino FROM conexoes WHERE masmorra_id = ? ORDER BY destino", (identificador,))]
    return masmorra


def mostrar_mapa(masmorra):
    salas = masmorra["salas"]
    min_x, max_x = min(s["x"] for s in salas), max(s["x"] for s in salas)
    min_y, max_y = min(s["y"] for s in salas), max(s["y"] for s in salas)
    grade = [[" "] * ((max_x - min_x) * 6 + 3) for _ in range((max_y - min_y) * 2 + 1)]
    posicoes = {}
    for sala in salas:
        x, y = (sala["x"] - min_x) * 6, (sala["y"] - min_y) * 2
        grade[y][x:x + 3] = list(f"[{sala['numero']}]")
        posicoes[sala["numero"]] = (x, y)
    for origem, destino in masmorra["conexoes"]:
        x1, y1 = posicoes[origem]
        x2, y2 = posicoes[destino]
        if y1 == y2:
            for x in range(min(x1, x2) + 3, max(x1, x2)):
                grade[y1][x] = "-"
        else:
            grade[(y1 + y2) // 2][x1 + 1] = "|"
    print("\n" + "\n".join("".join(linha).rstrip() for linha in grade))
    for sala in salas:
        print(f"  {sala['numero']}: {sala['nome']}")


def escolher(titulo, opcoes):
    print(f"\n{titulo}")
    for numero, opcao in enumerate(opcoes, 1):
        print(f"{numero}. {opcao}")
    while True:
        valor = input("> ").strip()
        if valor in [str(n) for n in range(1, len(opcoes) + 1)]:
            return opcoes[int(valor) - 1]
        print("Digite um dos números da lista.")


def explorar(masmorra):
    print("\n" + masmorra["historia"])
    print("Exploração narrativa: os encontros não têm combate nesta versão.")
    atual = 1
    visitadas = set()
    while True:
        sala = masmorra["salas"][atual - 1]
        print(f"\n[{atual}] {sala['nome']}")
        if atual not in visitadas:
            print(sala["evento"])
            visitadas.add(atual)
        if sala["nome"] == "Saída":
            print(f"Você escapou! Salas visitadas: {len(visitadas)}/5.")
            return
        destinos = vizinhos(atual, masmorra["conexoes"])
        print("Passagens: " + ", ".join(map(str, destinos)))
        valor = input("Número da sala, M para mapa ou V para voltar ao menu: ").strip().lower()
        if valor == "v":
            return
        if valor == "m":
            mostrar_mapa(masmorra)
        elif valor in [str(n) for n in destinos]:
            atual = int(valor)
        else:
            print("Não existe uma passagem para essa opção.")


def main():
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row
    try:
        criar_banco(conexao)
        while True:
            acao = escolher("ARQUITETO DE MASMORRAS", ["Gerar masmorra", "Listar masmorras", "Explorar masmorra", "Sair"])
            if acao == "Sair":
                break
            if acao == "Gerar masmorra":
                tema = escolher("Escolha o tema", list(TEMAS))
                dificuldade = escolher("Escolha a dificuldade", ["Tranquila", "Normal", "Perigosa"])
                semente = input("Semente (Enter para sortear): ").strip() or secrets.token_hex(4)
                masmorra = gerar_masmorra(tema, semente, dificuldade)
                identificador = salvar_masmorra(conexao, masmorra)
                print(f"\nMasmorra {identificador} salva! Semente: {semente}")
                print(masmorra["historia"])
                mostrar_mapa(masmorra)
            elif acao == "Listar masmorras":
                registros = conexao.execute("SELECT * FROM masmorras ORDER BY id DESC").fetchall()
                if not registros:
                    print("Nenhuma masmorra salva. Gere a primeira pelo menu!")
                for registro in registros:
                    print(f"{registro['id']}: {registro['tema']} | {registro['dificuldade']} | semente: {registro['semente']}")
            else:
                valor = input("ID da masmorra (use Listar para consultar): ").strip()
                if not valor.isascii() or not valor.isdigit() or len(valor) > 18:
                    print("Digite um ID numérico válido.")
                    continue
                masmorra = carregar_masmorra(conexao, int(valor))
                if masmorra is None:
                    print("Masmorra não encontrada.")
                else:
                    explorar(masmorra)
    except (KeyboardInterrupt, EOFError):
        print("\nAté a próxima aventura!")
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
