# Arquiteto de Masmorras — primeira versão

Um projeto para aprender Python e SQLite criando um pequeno jogo de exploração.
Esta versão roda no terminal. Não altera o Minecraft e ainda não exporta datapacks.

## Como executar no Windows

1. Abra a pasta que contém `main.py` no Explorador de Arquivos.
2. Clique na barra de endereço, digite `cmd` e pressione Enter.
3. Execute `python main.py`. Se seu computador usa o inicializador do Python, use `py main.py`.

Não há bibliotecas adicionais para instalar. O arquivo `masmorras.db` é criado
automaticamente ao lado do programa. Não apagar esse arquivo se quiser manter masmorras.

## Sua primeira aventura

1. Escolha **Gerar masmorra**.
2. Selecione **Biblioteca amaldiçoada**, dificuldade **Normal** e semente `luana`.
3. Observe o mapa: os números identificam salas; linhas são passagens reais.
4. Escolha **Listar masmorras** para consultar o ID salvo.
5. Escolha **Explorar masmorra** e informe esse ID.
6. Digite o número de uma sala vizinha para andar. Use `M` para ver o mapa ou `V` para sair.

A saída fica em uma sala com a maior distância da entrada. Tesouros podem estar
em ramificações opcionais. Inimigos e armadilhas são encontros narrativos;
a dificuldade altera a quantidade descrita de inimigos, sem combate ou vida ainda.
O mapa revela todas as salas nesta versão. O progresso da exploração não é salvo;
a estrutura da masmorra fica salva e pode ser explorada novamente.

## Como o banco funciona

| Tabela | O que guarda |
| --- | --- |
| masmorras | ID, tema, semente, dificuldade, história e data em UTC |
| salas | Nome, coordenadas e evento de cada sala |
| conexoes | Pares de salas com passagem entre elas |

O `masmorra_id` relaciona cada sala à sua masmorra. Cada conexão referencia duas
salas da mesma masmorra. As passagens funcionam nos dois sentidos.
Os pontos de interrogação nas consultas recebem os valores separadamente do SQL.
O bloco `with conexao` faz a gravação inteira funcionar como uma transação.

Nesta etapa, os catálogos de temas ficam no código. Transferi-los para tabelas é
um exercício posterior, quando inserir e consultar dados já estiver familiar.


