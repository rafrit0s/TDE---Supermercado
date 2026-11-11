from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura'

def conectar_db():
    return sqlite3.connect('supermercado.db')

# Cliente

@app.route('/')
def loja():
    conexao = conectar_db()
    produtos = conexao.execute('SELECT * FROM produtos WHERE quantidade > 0').fetchall()
    conexao.close()
    
    if 'carrinho' not in session:
        session['carrinho'] = {}
        
    total_itens = sum(item['quantidade'] for item in session['carrinho'].values())
    return render_template('loja.html', produtos=produtos, total_itens=total_itens)

@app.route('/add_carrinho', methods=['POST'])
def add_carrinho():
    produto_id = request.form['produto_id']
    quantidade = int(request.form['quantidade'])
    
    conexao = conectar_db()
    produto = conexao.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
    conexao.close()
    
    if produto:
        carrinho = session.get('carrinho', {})
        estoque_disponivel = produto[3]
        
        qtd_atual = carrinho.get(produto_id, {}).get('quantidade', 0)
        nova_qtd = qtd_atual + quantidade
        
        if nova_qtd > estoque_disponivel:
            flash('Estoque insuficiente para esta quantidade.', 'danger')
        else:
            carrinho[produto_id] = {
                'nome': produto[1],
                'preco': produto[2],
                'quantidade': nova_qtd,
                'imagem': produto[4]
            }
            session['carrinho'] = carrinho
            session.modified = True
            flash(f'{produto[1]} adicionado ao carrinho!', 'success')
            
    return redirect(url_for('loja'))

@app.route('/remover_carrinho/<produto_id>')
def remover_carrinho(produto_id):
    carrinho = session.get('carrinho', {})
    if produto_id in carrinho:
        del carrinho[produto_id]
        session['carrinho'] = carrinho
        session.modified = True
    return redirect(url_for('ver_carrinho'))

@app.route('/carrinho')
def ver_carrinho():
    carrinho = session.get('carrinho', {})
    subtotal = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
    
    desconto = 0
    if subtotal > 200:
        desconto = subtotal * 0.05
        
    total_final = subtotal - desconto
    return render_template('carrinho.html', carrinho=carrinho, subtotal=subtotal, desconto=desconto, total=total_final)

@app.route('/finalizar_compra', methods=['POST'])
def finalizar_compra():
    carrinho = session.get('carrinho', {})
    if not carrinho:
        return redirect(url_for('loja'))
        
    metodo_pagamento = request.form['pagamento']
    subtotal = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
    desconto = subtotal * 0.05 if subtotal > 200 else 0
    total_final = subtotal - desconto
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    conexao = conectar_db()
    cursor = conexao.cursor()
    
    cursor.execute('INSERT INTO vendas (data_hora, total, desconto, metodo_pagamento) VALUES (?, ?, ?, ?)',
                   (data_hora, total_final, desconto, metodo_pagamento))
    venda_id = cursor.lastrowid
    
    for p_id, item in carrinho.items():
        cursor.execute('INSERT INTO itens_venda (venda_id, produto_nome, quantidade, preco_unitario) VALUES (?, ?, ?, ?)',
                       (venda_id, item['nome'], item['quantidade'], item['preco']))
        
        cursor.execute('UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?', (item['quantidade'], int(p_id)))
        
    conexao.commit()
    conexao.close()
    
    dados_recibo = {
        'id': venda_id,
        'data': data_hora,
        'itens': carrinho,
        'subtotal': subtotal,
        'desconto': desconto,
        'total': total_final,
        'metodo': metodo_pagamento
    }
    session['carrinho'] = {}
    
    return render_template('recibo.html', recibo=dados_recibo)

# Admin

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']
        if senha == 'admin123':
            session['logado'] = True
            return redirect(url_for('admin'))
        else:
            flash('Senha incorreta!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('loja'))

@app.route('/admin')
def admin():
    if not session.get('logado'):
        return redirect(url_for('login'))
        
    conexao = conectar_db()
    produtos = conexao.execute('SELECT * FROM produtos').fetchall()
    conexao.close()
    return render_template('admin.html', produtos=produtos)

@app.route('/admin/historico')
def historico():
    if not session.get('logado'):
        return redirect(url_for('login'))
        
    conexao = conectar_db()
    vendas = conexao.execute('SELECT * FROM vendas ORDER BY id DESC').fetchall()
    conexao.close()
    return render_template('historico.html', vendas=vendas)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    if not session.get('logado'): return redirect(url_for('login'))
    
    nome = request.form['nome']
    preco = float(request.form['preco'])
    quantidade = int(request.form['quantidade'])
    imagem_url = request.form['imagem_url']
    
    conexao = conectar_db()
    conexao.execute('INSERT INTO produtos (nome, preco, quantidade, imagem_url) VALUES (?, ?, ?, ?)', 
                    (nome, preco, quantidade, imagem_url))
    conexao.commit()
    conexao.close()
    return redirect(url_for('admin'))

@app.route('/deletar/<int:id>')
def deletar(id):
    if not session.get('logado'): return redirect(url_for('login'))
    conexao = conectar_db()
    conexao.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conexao.commit()
    conexao.close()
    return redirect(url_for('admin'))

@app.route('/editar/<int:id>')
def editar(id):
    if not session.get('logado'): return redirect(url_for('login'))
    
    conexao = conectar_db()

    produto = conexao.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
    conexao.close()
    
    return render_template('editar.html', produto=produto)

@app.route('/atualizar/<int:id>', methods=['POST'])
def atualizar(id):
    if not session.get('logado'): return redirect(url_for('login'))
    
    nome = request.form['nome']
    preco = float(request.form['preco'])
    quantidade = int(request.form['quantidade'])
    imagem_url = request.form['imagem_url']
    
    conexao = conectar_db()

    conexao.execute('''
        UPDATE produtos 
        SET nome = ?, preco = ?, quantidade = ?, imagem_url = ? 
        WHERE id = ?
    ''', (nome, preco, quantidade, imagem_url, id))
    conexao.commit()
    conexao.close()
    
    return redirect(url_for('admin'))
@app.route('/admin/recibo/<int:venda_id>')
def ver_recibo_admin(venda_id):
    if not session.get('logado'): return redirect(url_for('login'))
    
    conexao = conectar_db()

    venda = conexao.execute('SELECT * FROM vendas WHERE id = ?', (venda_id,)).fetchone()
    
    if not venda:
        conexao.close()
        flash('Venda não encontrada.', 'danger')
        return redirect(url_for('historico'))
        
    itens_db = conexao.execute('SELECT * FROM itens_venda WHERE venda_id = ?', (venda_id,)).fetchall()
    conexao.close()
    
    subtotal = venda[2] + venda[3]
    
    itens_formatados = {}
    for i, item in enumerate(itens_db):
        itens_formatados[str(i)] = {
            'nome': item[2],
            'quantidade': item[3],
            'preco': item[4]
        }
        
    dados_recibo = {
        'id': venda[0],
        'data': venda[1],
        'itens': itens_formatados,
        'subtotal': subtotal,
        'desconto': venda[3],
        'total': venda[2],
        'metodo': venda[4]
    }
    
    return render_template('recibo_admin.html', recibo=dados_recibo)

if __name__ == '__main__':
    app.run(debug=True)
    