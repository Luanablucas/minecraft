import contextlib
import importlib.util
import io
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

arquivo = Path('outputs/arquiteto_masmorras/main.py').resolve()
spec = importlib.util.spec_from_file_location('masmorras', arquivo)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for tema in m.TEMAS:
    for dificuldade in ('Tranquila', 'Normal', 'Perigosa'):
        for seed in range(100):
            d = m.gerar_masmorra(tema, str(seed), dificuldade)
            assert d == m.gerar_masmorra(tema, str(seed), dificuldade)
            assert len(d['salas']) == 5
            assert len({(s['x'], s['y']) for s in d['salas']}) == 5
            visitadas = {1}
            for _ in range(5):
                for n in list(visitadas):
                    visitadas.update(m.vizinhos(n, d['conexoes']))
            assert len(visitadas) == 5
            assert sum(s['nome'] == 'Saída' for s in d['salas']) == 1
            assert sum('Tesouro encontrado' in s['evento'] for s in d['salas']) == 1
            for a, b in d['conexoes']:
                sa, sb = d['salas'][a - 1], d['salas'][b - 1]
                assert abs(sa['x'] - sb['x']) + abs(sa['y'] - sb['y']) == 1
            with contextlib.redirect_stdout(io.StringIO()):
                m.mostrar_mapa(d)

with tempfile.TemporaryDirectory() as pasta:
    m.BANCO = Path(pasta) / 'teste.db'
    c = sqlite3.connect(m.BANCO)
    c.row_factory = sqlite3.Row
    m.criar_banco(c)
    d = m.gerar_masmorra('Biblioteca amaldiçoada', 'luana')
    ident = m.salvar_masmorra(c, d)
    c.close()
    c = sqlite3.connect(m.BANCO)
    c.row_factory = sqlite3.Row
    volta = m.carregar_masmorra(c, ident)
    assert volta['conexoes'] == d['conexoes']
    for original, salva in zip(d['salas'], volta['salas']):
        assert all(salva[k] == v for k, v in original.items())
    assert m.carregar_masmorra(c, 99999) is None
    c.close()
    entradas = ['2', '1', '1', '2', 'teste', '3', '999', '3', '1', 'm', 'v', '4']
    with patch('builtins.input', side_effect=entradas), contextlib.redirect_stdout(io.StringIO()) as saida:
        m.main()
    assert 'Masmorra 2 salva' in saida.getvalue()
    assert 'Masmorra não encontrada' in saida.getvalue()
print('OK: 900 mapas, sementes, conectividade, persistência e fluxo do menu.')
