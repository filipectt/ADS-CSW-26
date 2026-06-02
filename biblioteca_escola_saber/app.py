import pyodbc
from flask import Flask, jsonify, request, render_template
from datetime import datetime

app = Flask(__name__)

DB_CONFIG = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-PATLR5R\\SQLEXPRESS;"
    "DATABASE=Biblioteca;"
    "Trusted_Connection=yes;"
)

def get_db_connection():
    return pyodbc.connect(DB_CONFIG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ALUNO")
    alunos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM LIVRO")
    livros = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM EMPRESTIMO WHERE status != 'Devolvido'")
    emprestimos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM EXEMPLAR WHERE status = 'Disponivel'")
    disponiveis = cursor.fetchone()[0]
    conn.close()
    return jsonify({
        "total_alunos": alunos,
        "total_livros": livros,
        "emprestimos_ativos": emprestimos,
        "exemplares_disponiveis": disponiveis
    })

@app.route('/api/alunos', methods=['GET'])
def get_alunos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_aluno, nome, matricula, email, telefone, curso, data_cadastro, status FROM ALUNO")
    columns = [column[0] for column in cursor.description]
    data = []
    for row in cursor.fetchall():
        row_dict = dict(zip(columns, row))
        if row_dict['data_cadastro']:
            row_dict['data_cadastro'] = row_dict['data_cadastro'].strftime('%Y-%m-%d')
        data.append(row_dict)
    conn.close()
    return jsonify(data)

@app.route('/api/alunos', methods=['POST'])
def create_aluno():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ALUNO (nome, matricula, email, telefone, curso, data_cadastro, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data['nome'], data['matricula'], data['email'], data['telefone'], data['curso'], data['data_cadastro'], data['status'])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Aluno criado com sucesso!"}), 201

@app.route('/api/alunos/<int:id_aluno>', methods=['PUT'])
def update_aluno(id_aluno):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE ALUNO SET nome=?, matricula=?, email=?, telefone=?, curso=?, data_cadastro=?, status=? WHERE id_aluno=?",
        (data['nome'], data['matricula'], data['email'], data['telefone'], data['curso'], data['data_cadastro'], data['status'], id_aluno)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Aluno atualizado com sucesso!"})

@app.route('/api/alunos/<int:id_aluno>', methods=['DELETE'])
def delete_aluno(id_aluno):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ALUNO WHERE id_aluno=?", (id_aluno,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Aluno excluído com sucesso!"})

@app.route('/api/autores', methods=['GET'])
def get_autores():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_autor, nome, nacionalidade FROM AUTOR")
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)

@app.route('/api/autores', methods=['POST'])
def create_autor():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO AUTOR (nome, nacionalidade) VALUES (?, ?)", (data['nome'], data['nacionalidade']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Autor criado com sucesso!"}), 201

@app.route('/api/autores/<int:id_autor>', methods=['PUT'])
def update_autor(id_autor):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE AUTOR SET nome=?, nacionalidade=? WHERE id_autor=?", (data['nome'], data['nacionalidade'], id_autor))
    conn.commit()
    conn.close()
    return jsonify({"message": "Autor atualizado com sucesso!"})

@app.route('/api/autores/<int:id_autor>', methods=['DELETE'])
def delete_autor(id_autor):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM AUTOR WHERE id_autor=?", (id_autor,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Autor excluído com sucesso!"})

@app.route('/api/areas', methods=['GET'])
def get_areas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_area, nome_area, descricao FROM AREA_CONHECIMENTO")
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)

@app.route('/api/areas', methods=['POST'])
def create_area():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO AREA_CONHECIMENTO (nome_area, descricao) VALUES (?, ?)", (data['nome_area'], data['descricao']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Área criada com sucesso!"}), 201

@app.route('/api/areas/<int:id_area>', methods=['PUT'])
def update_area(id_area):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE AREA_CONHECIMENTO SET nome_area=?, descricao=? WHERE id_area=?", (data['nome_area'], data['descricao'], id_area))
    conn.commit()
    conn.close()
    return jsonify({"message": "Área actualizada com sucesso!"})

@app.route('/api/areas/<int:id_area>', methods=['DELETE'])
def delete_area(id_area):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM AREA_CONHECIMENTO WHERE id_area=?", (id_area,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Área excluída com sucesso!"})

@app.route('/api/livros', methods=['GET'])
def get_livros():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT l.id_livro, l.titulo, l.isbn, l.editora, l.ano_publicacao,
               (SELECT TOP 1 a.nome FROM AUTOR a JOIN LIVRO_AUTOR la ON a.id_autor = la.fk_autor WHERE la.fk_livro = l.id_livro) as nome_autor,
               (SELECT TOP 1 ar.nome_area FROM AREA_CONHECIMENTO ar JOIN LIVRO_AREA lr ON ar.id_area = lr.fk_area WHERE lr.fk_livro = l.id_livro) as nome_area,
               (SELECT COUNT(*) FROM EXEMPLAR e WHERE e.fk_livro = l.id_livro AND e.status = 'Disponivel') as exemplares_disponiveis,
               (SELECT TOP 1 la.fk_autor FROM LIVRO_AUTOR la WHERE la.fk_livro = l.id_livro) as fk_autor,
               (SELECT TOP 1 lr.fk_area FROM LIVRO_AREA lr WHERE lr.fk_livro = l.id_livro) as fk_area
        FROM LIVRO l
    """
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)

@app.route('/api/livros', methods=['POST'])
def create_livro():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO LIVRO (titulo, isbn, editora, ano_publicacao) OUTPUT INSERTED.id_livro VALUES (?, ?, ?, ?)",
        (data['titulo'], data['isbn'], data['editora'], data['ano_publicacao'])
    )
    id_livro = cursor.fetchone()[0]
    
    if data.get('fk_autor'):
        cursor.execute("INSERT INTO LIVRO_AUTOR (fk_livro, fk_autor) VALUES (?, ?)", (id_livro, data['fk_autor']))
    if data.get('fk_area'):
        cursor.execute("INSERT INTO LIVRO_AREA (fk_livro, fk_area) VALUES (?, ?)", (id_livro, data['fk_area']))
        
    conn.commit()
    conn.close()
    return jsonify({"message": "Livro criado com sucesso!"}), 201

@app.route('/api/livros/<int:id_livro>', methods=['PUT'])
def update_livro(id_livro):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE LIVRO SET titulo=?, isbn=?, editora=?, ano_publicacao=? WHERE id_livro=?",
        (data['titulo'], data['isbn'], data['editora'], data['ano_publicacao'], id_livro)
    )
    cursor.execute("DELETE FROM LIVRO_AUTOR WHERE fk_livro=?", (id_livro,))
    if data.get('fk_autor'):
        cursor.execute("INSERT INTO LIVRO_AUTOR (fk_livro, fk_autor) VALUES (?, ?)", (id_livro, data['fk_autor']))
        
    cursor.execute("DELETE FROM LIVRO_AREA WHERE fk_livro=?", (id_livro,))
    if data.get('fk_area'):
        cursor.execute("INSERT INTO LIVRO_AREA (fk_livro, fk_area) VALUES (?, ?)", (id_livro, data['fk_area']))
        
    conn.commit()
    conn.close()
    return jsonify({"message": "Livro atualizado com sucesso!"})

@app.route('/api/livros/<int:id_livro>', methods=['DELETE'])
def delete_livro(id_livro):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM LIVRO_AUTOR WHERE fk_livro=?", (id_livro,))
    cursor.execute("DELETE FROM LIVRO_AREA WHERE fk_livro=?", (id_livro,))
    cursor.execute("DELETE FROM LIVRO WHERE id_livro=?", (id_livro,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Livro excluído com sucesso!"})

@app.route('/api/exemplares', methods=['GET'])
def get_exemplares():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT e.id_exemplar, e.codigo_exemplar, e.status, e.fk_livro, l.titulo as titulo_livro 
        FROM EXEMPLAR e
        JOIN LIVRO l ON e.fk_livro = l.id_livro
    """
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)

@app.route('/api/exemplares', methods=['POST'])
def create_exemplar():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO EXEMPLAR (codigo_exemplar, status, fk_livro) VALUES (?, ?, ?)",
        (data['codigo_exemplar'], data['status'], data['fk_livro'])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Exemplar criado com sucesso!"}), 201

@app.route('/api/exemplares/<int:id_exemplar>', methods=['PUT'])
def update_exemplar(id_exemplar):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE EXEMPLAR SET codigo_exemplar=?, status=?, fk_livro=? WHERE id_exemplar=?",
        (data['codigo_exemplar'], data['status'], data['fk_livro'], id_exemplar)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Exemplar atualizado com sucesso!"})

@app.route('/api/exemplares/<int:id_exemplar>', methods=['DELETE'])
def delete_exemplar(id_exemplar):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM EXEMPLAR WHERE id_exemplar=?", (id_exemplar,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Exemplar excluído com sucesso!"})

@app.route('/api/emprestimos', methods=['GET'])
def get_emprestimos():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT emp.id_emprestimo, emp.fk_aluno, emp.fk_exemplar, emp.data_emprestimo, 
               emp.data_prevista_devolucao, emp.data_devolucao, emp.status,
               al.nome as nome_aluno, ex.codigo_exemplar, liv.titulo as titulo_livro
        FROM EMPRESTIMO emp
        JOIN ALUNO al ON emp.fk_aluno = al.id_aluno
        JOIN EXEMPLAR ex ON emp.fk_exemplar = ex.id_exemplar
        JOIN LIVRO liv ON ex.fk_livro = liv.id_livro
    """
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    data = []
    for row in cursor.fetchall():
        row_dict = dict(zip(columns, row))
        if row_dict['data_emprestimo']:
            row_dict['data_emprestimo'] = row_dict['data_emprestimo'].strftime('%Y-%m-%d')
        if row_dict['data_prevista_devolucao']:
            row_dict['data_prevista_devolucao'] = row_dict['data_prevista_devolucao'].strftime('%Y-%m-%d')
        if row_dict['data_devolucao']:
            row_dict['data_devolucao'] = row_dict['data_devolucao'].strftime('%Y-%m-%d')
        data.append(row_dict)
    conn.close()
    return jsonify(data)

@app.route('/api/emprestimos', methods=['POST'])
def create_emprestimo():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT status FROM EXEMPLAR WHERE id_exemplar = ?", (data['fk_exemplar'],))
    exemplar = cursor.fetchone()
    if not exemplar:
        conn.close()
        return jsonify({"error": "Exemplar físico não encontrado no banco!"}), 404
    if exemplar[0] != 'Disponivel':
        conn.close()
        return jsonify({"error": "Este exemplar físico já se encontra emprestado!"}), 400

    cursor.execute(
        "INSERT INTO EMPRESTIMO (fk_aluno, fk_exemplar, data_emprestimo, data_prevista_devolucao, data_devolucao, status) VALUES (?, ?, ?, ?, NULL, ?)",
        (data['fk_aluno'], data['fk_exemplar'], data['data_emprestimo'], data['data_prevista_devolucao'], data['status'])
    )
    
    cursor.execute("UPDATE EXEMPLAR SET status = 'Emprestado' WHERE id_exemplar = ?", (data['fk_exemplar'],))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Empréstimo registrado com sucesso e exemplar baixado!"}), 201

@app.route('/api/emprestimos/<int:id_emprestimo>', methods=['PUT'])
def update_emprestimo(id_emprestimo):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT fk_exemplar, status FROM EMPRESTIMO WHERE id_emprestimo = ?", (id_emprestimo,))
    loan_atual = cursor.fetchone()
    if not loan_atual:
        conn.close()
        return jsonify({"error": "Empréstimo não encontrado!"}), 404
        
    exemplar_antigo = loan_atual[0]
    status_antigo = loan_atual[1]
    
    exemplar_novo = int(data['fk_exemplar'])
    status_novo = data['status']
    data_devolucao = data.get('data_devolucao') or None
    
    if exemplar_antigo != exemplar_novo:
        cursor.execute("UPDATE EXEMPLAR SET status = 'Disponivel' WHERE id_exemplar = ?", (exemplar_antigo,))
        cursor.execute("SELECT status FROM EXEMPLAR WHERE id_exemplar = ?", (exemplar_novo,))
        status_novo_ex = cursor.fetchone()
        if status_novo_ex and status_novo_ex[0] != 'Disponivel' and status_novo != 'Devolvido':
            conn.rollback()
            conn.close()
            return jsonify({"error": "O novo exemplar selecionado está indisponível!"}), 400
        if status_novo != 'Devolvido':
            cursor.execute("UPDATE EXEMPLAR SET status = 'Emprestado' WHERE id_exemplar = ?", (exemplar_novo,))

    if status_novo == 'Devolvido' and status_antigo != 'Devolvido':
        cursor.execute("UPDATE EXEMPLAR SET status = 'Disponivel' WHERE id_exemplar = ?", (exemplar_novo,))
        if not data_devolucao:
            data_devolucao = datetime.now().strftime('%Y-%m-%d')
    elif status_novo != 'Devolvido' and status_antigo == 'Devolvido':
        cursor.execute("UPDATE EXEMPLAR SET status = 'Emprestado' WHERE id_exemplar = ?", (exemplar_novo,))
        data_devolucao = None

    cursor.execute(
        "UPDATE EMPRESTIMO SET fk_aluno=?, fk_exemplar=?, data_emprestimo=?, data_prevista_devolucao=?, data_devolucao=?, status=? WHERE id_emprestimo=?",
        (data['fk_aluno'], exemplar_novo, data['data_emprestimo'], data['data_prevista_devolucao'], data_devolucao, status_novo, id_emprestimo)
    )
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Empréstimo e estoque reajustados perfeitamente!"})

@app.route('/api/emprestimos/<int:id_emprestimo>', methods=['DELETE'])
def delete_emprestimo(id_emprestimo):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT fk_exemplar, status FROM EMPRESTIMO WHERE id_emprestimo = ?", (id_emprestimo,))
    loan = cursor.fetchone()
    if loan and loan[1] != 'Devolvido':
        cursor.execute("UPDATE EXEMPLAR SET status = 'Disponivel' WHERE id_exemplar = ?", (loan[0],))
            
    cursor.execute("DELETE FROM EMPRESTIMO WHERE id_emprestimo=?", (id_emprestimo,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Empréstimo deletado e estoque retornado à prateleira!"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)