import sqlite3

conexao = sqlite3.connect('supermercado.db')
cursor = conexao.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL,
        quantidade INTEGER NOT NULL,
        imagem_url TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora TEXT NOT NULL,
        total REAL NOT NULL,
        desconto REAL NOT NULL,
        metodo_pagamento TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS itens_venda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER,
        produto_nome TEXT,
        quantidade INTEGER,
        preco_unitario REAL,
        FOREIGN KEY(venda_id) REFERENCES vendas(id)
    )
''')

conexao.commit()
conexao.close()
print("Banco de dados NG+ criado com sucesso!")