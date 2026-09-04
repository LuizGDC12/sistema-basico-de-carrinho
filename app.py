from flask import Flask, request, session, redirect, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = "qualquer_frase_secreta_aqui"

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="luizgustavoBR12",
        database="carrinho_compras"
    )

@app.route("/")
def home():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, valor, quantidade_estoque FROM produtos")
    produtos = cursor.fetchall()
    conexao.close()

    if "nome" in session:
        cabecalho = f"<p>Logado como {session['nome']} | <a href='/carrinho'>Ver carrinho</a> | <a href='/logout'>Sair</a></p>"
    else:
        cabecalho = "<p><a href='/login'>Login</a> | <a href='/cadastro'>Criar conta</a></p>"

    resposta = cabecalho + "<h1>Produtos da loja</h1><ul>"
    for id_produto, nome, valor, estoque in produtos:
        resposta += f"<li>{nome} - R$ {valor} (estoque: {estoque}) "
        if "id_cliente" in session:
            resposta += f"<a href='/carrinho/adicionar/{id_produto}'>Adicionar ao carrinho</a>"
        resposta += "</li>"
    resposta += "</ul>"
    return resposta

    

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, email, senha) VALUES (%s, %s, %s)",
            (nome, email, senha)
        )
        conexao.commit()
        conexao.close()

        return "<h2>Conta criada com sucesso!</h2><a href='/login'>Ir para o login</a>"

    return """
    <h1>Criar conta</h1>
    <form method="POST">
        Nome: <input type="text" name="nome"><br>
        Email: <input type="text" name="email"><br>
        Senha: <input type="password" name="senha"><br>
        <input type="submit" value="Criar conta">
    </form>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id, nome FROM clientes WHERE email = %s AND senha = %s",
            (email, senha)
        )
        resultado = cursor.fetchone()
        conexao.close()

        if resultado:
            id_cliente, nome = resultado
            session["id_cliente"] = id_cliente
            session["nome"] = nome
            return redirect(url_for("home"))
        else:
            return "<h2>Email ou senha incorretos.</h2><a href='/login'>Tentar novamente</a>"

    return """
    <h1>Login</h1>
    <form method="POST">
        Email: <input type="text" name="email"><br>
        Senha: <input type="password" name="senha"><br>
        <input type="submit" value="Entrar">
    </form>
    """

@app.route("/carrinho/adicionar/<int:id_produto>")
def adicionar_carrinho(id_produto):
    if "id_cliente" not in session:
        return redirect(url_for("login"))

    id_cliente = session["id_cliente"]
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO carrinho (id_cliente, id_produto, quantidade) VALUES (%s, %s, 1)",
        (id_cliente, id_produto)
    )
    conexao.commit()
    conexao.close()
    return redirect(url_for("home"))


@app.route("/carrinho")
def ver_carrinho():
    if "id_cliente" not in session:
        return redirect(url_for("login"))

    id_cliente = session["id_cliente"]
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT p.nome, p.valor, ca.quantidade, (p.valor * ca.quantidade) AS subtotal
        FROM carrinho ca
        JOIN produtos p ON ca.id_produto = p.id
        WHERE ca.id_cliente = %s
    """, (id_cliente,))
    itens = cursor.fetchall()
    conexao.close()

    total = sum(item[3] for item in itens)

    resposta = "<h1>Seu carrinho</h1><ul>"
    for nome, valor, quantidade, subtotal in itens:
        resposta += f"<li>{nome} - R$ {valor} x {quantidade} = R$ {subtotal:.2f}</li>"
    resposta += f"</ul><p>Total: R$ {total:.2f}</p><a href='/'>Voltar</a>"
    return resposta


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)