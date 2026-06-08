from flask import Flask, request, jsonify, render_template
import pyodbc
from datetime import date, datetime

app = Flask(__name__)

# Configuração da conexão com o SQL Server (Ajuste o SERVER conforme seu ambiente)
DB_CONFIG = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;' # Mude para seu servidor SQL
    'DATABASE=BibliotecaEscolaSaber;'
    'Trusted_Connection=yes;'
)

def get_conn():
    return pyodbc.connect(DB_CONFIG)

def serialize_row(row, cursor):
    """Converte a linha do banco em dicionário e trata tipos de data."""
    columns = [column[0] for column in cursor.description]
    obj = dict(zip(columns, row))
    for key, value in obj.items():
        if isinstance(value, (date, datetime)):
            obj[key] = value.strftime('%Y-%m-%d')
    return obj

# ==========================================
# ROTA PRINCIPAL (Renderiza o HTML da pasta templates)
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# DASHBOARD
# ==========================================
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as t FROM ALUNO WHERE status = 'ATIVO'")
            total_alunos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as t FROM LIVRO")
            total_livros = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as t FROM EMPRESTIMO WHERE status IN ('ATIVO', 'ATRASADO')")
            emprestimos_ativos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as t FROM EXEMPLAR WHERE status = 'DISPONIVEL'")
            exemplares_disp = cursor.fetchone()[0]
            
            return jsonify({
                "total_alunos": total_alunos,
                "total_livros": total_livros,
                "emprestimos_ativos": emprestimos_ativos,
                "exemplares_disponiveis": exemplares_disp
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# CURSOS (Para o dropdown do Aluno)
# ==========================================
@app.route('/api/cursos', methods=['GET'])
def get_cursos():
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_curso, nome_curso FROM CURSO")
        return jsonify([serialize_row(r, cursor) for r in cursor.fetchall()])

# ==========================================
# ALUNOS
# ==========================================
@app.route('/api/alunos', methods=['GET', 'POST'])
def handle_alunos():
    if request.method == 'GET':
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.id_aluno, a.nome, a.matricula, a.email, a.telefone, 
                       a.fk_curso, c.nome_curso as curso, a.data_cadastro, a.status 
                FROM ALUNO a
                LEFT JOIN CURSO c ON a.fk_curso = c.id_curso
            """)
            return jsonify([serialize_row(r, cursor) for r in cursor.fetchall()])
            
    if request.method == 'POST':
        data = request.json
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("EXEC SP_CADASTRAR_ALUNO @nome=?, @matricula=?, @email=?, @telefone=?, @fk_curso=?",
                               (data['nome'], data['matricula'], data['email'], data['telefone'], data['fk_curso']))
                conn.commit()
            return jsonify({"message": "Aluno cadastrado com sucesso!"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route('/api/alunos/<int:id>', methods=['PUT', 'DELETE'])
def update_aluno(id):
    if request.method == 'PUT':
        data = request.json
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ALUNO SET nome=?, matricula=?, email=?, telefone=?, fk_curso=?, status=? 
                WHERE id_aluno=?
            """, (data['nome'], data['matricula'], data['email'], data['telefone'], data['fk_curso'], data['status'], id))
            conn.commit()
        return jsonify({"message": "Aluno atualizado com sucesso!"})
        
    if request.method == 'DELETE':
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ALUNO WHERE id_aluno=?", (id,))
                conn.commit()
            return jsonify({"message": "Aluno excluído com sucesso!"})
        except Exception as e:
            return jsonify({"error": "Erro de FK. Aluno possui vínculos."}), 400

# ==========================================
# LIVROS
# ==========================================
@app.route('/api/livros', methods=['GET', 'POST'])
def handle_livros():
    if request.method == 'GET':
        with get_conn() as conn:
            cursor = conn.cursor()
            query = """
                SELECT l.id_livro, l.titulo, l.isbn, l.editora, l.ano_publicacao,
                       (SELECT TOP 1 au.nome FROM LIVRO_AUTOR la JOIN AUTOR au ON la.fk_autor = au.id_autor WHERE la.fk_livro = l.id_livro) as nome_autor,
                       (SELECT TOP 1 ar.nome_area FROM LIVRO_AREA l_ar JOIN AREA_CONHECIMENTO ar ON l_ar.fk_area = ar.id_area WHERE l_ar.fk_livro = l.id_livro) as nome_area,
                       (SELECT COUNT(*) FROM EXEMPLAR e WHERE e.fk_livro = l.id_livro AND e.status = 'DISPONIVEL') as exemplares_disponiveis
                FROM LIVRO l
            """
            cursor.execute(query)
            return jsonify([serialize_row(r, cursor) for r in cursor.fetchall()])
            
    if request.method == 'POST':
        data = request.json
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("EXEC SP_CADASTRAR_LIVRO @titulo=?, @isbn=?, @editora=?, @ano_publicacao=?",
                               (data['titulo'], data.get('isbn'), data.get('editora'), data.get('ano_publicacao')))
                cursor.execute("SELECT @@IDENTITY")
                id_livro = int(cursor.fetchone()[0])
                
                if data.get('fk_autor'):
                    cursor.execute("INSERT INTO LIVRO_AUTOR (fk_livro, fk_autor) VALUES (?, ?)", (id_livro, data['fk_autor']))
                if data.get('fk_area'):
                    cursor.execute("INSERT INTO LIVRO_AREA (fk_livro, fk_area) VALUES (?, ?)", (id_livro, data['fk_area']))
                conn.commit()
            return jsonify({"message": "Livro cadastrado com sucesso!"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route('/api/livros/<int:id>', methods=['PUT', 'DELETE'])
def update_livro(id):
    if request.method == 'PUT':
        data = request.json
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE LIVRO SET titulo=?, isbn=?, editora=?, ano_publicacao=? WHERE id_livro=?",
                           (data['titulo'], data.get('isbn'), data.get('editora'), data.get('ano_publicacao'), id))
            conn.commit()
        return jsonify({"message": "Livro atualizado com sucesso!"})
        
    if request.method == 'DELETE':
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM LIVRO_AUTOR WHERE fk_livro=?", (id,))
            cursor.execute("DELETE FROM LIVRO_AREA WHERE fk_livro=?", (id,))
            cursor.execute("DELETE FROM LIVRO WHERE id_livro=?", (id,))
            conn.commit()
        return jsonify({"message": "Livro excluído com sucesso!"})

# ==========================================
# AUTORES E ÁREAS
# ==========================================
@app.route('/api/autores', methods=['GET', 'POST'])
def handle_autores():
    if request.method == 'GET':
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM AUTOR")
            return jsonify([serialize_row(r, cursor) for r in cursor.fetchall()])
    if request.method == 'POST':
        data = request.json
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO AUTOR (nome, nacionalidade) VALUES (?, ?)", (data['nome'], data.get('nacionalidade')))
            conn.commit()
        return jsonify({"message": "Autor salvo!"}), 201

@app.route('/api/areas', methods=['GET', 'POST'])
def handle_areas():
    if request.method == 'GET':
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM AREA_CONHECIMENTO")
            return jsonify([serialize_row(r, cursor) for r in cursor.fetchall()])
    if request.method == 'POST':
        data = request.json
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO AREA_CONHECIMENTO (nome_area, descricao) VALUES (?, ?)", (data['nome_area'], data.get('descricao')))
            conn.commit()
        return jsonify({"message": "Área salva!"}), 201

@app.route('/api/autores/<int:id>', methods=['DELETE'])
def delete_autor(id):
    with get_conn() as conn:
        conn.execute("DELETE FROM AUTOR WHERE id_autor=?", (id,)).commit()
    return jsonify({"message": "Excluído!"})

@app.route('/api/areas/<int:id>', methods=['DELETE'])
def delete_area(id):
    with get_conn() as conn:
        conn.execute("DELETE FROM AREA_CONHECIMENTO WHERE id_area=?", (id,)).commit()
    return jsonify({"message": "Excluído!"})

# ==========================================
# EXEMPLARES
# ==========================================
@app.route('/api/exemplares', methods=['GET', 'POST'])
def handle_exemplares():
    if request.method == 'GET':
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id_exemplar, e.codigo_exemplar, e.status, l.titulo as titulo_livro
                FROM EXEMPLAR e JOIN LIVRO l ON e.fk_livro = l.id_livro
            """)
            return jsonify([serialize_row(r, cursor) for r in cursor.fetchall()])
            
    if request.method == 'POST':
        data = request.json
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("EXEC SP_CADASTRAR_EXEMPLAR @codigo_exemplar=?, @fk_livro=?",
                               (data['codigo_exemplar'], data['fk_livro']))
                conn.commit()
            return jsonify({"message": "Exemplar cadastrado!"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route('/api/exemplares/<int:id>', methods=['PUT', 'DELETE'])
def update_exemplar(id):
    if request.method == 'PUT':
        data = request.json
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE EXEMPLAR SET codigo_exemplar=?, fk_livro=?, status=? WHERE id_exemplar=?",
                           (data['codigo_exemplar'], data['fk_livro'], data['status'], id))
            conn.commit()
        return jsonify({"message": "Exemplar atualizado!"})
    if request.method == 'DELETE':
        with get_conn() as conn:
            conn.execute("DELETE FROM EXEMPLAR WHERE id_exemplar=?", (id,)).commit()
        return jsonify({"message": "Excluído!"})

# ==========================================
# EMPRÉSTIMOS
# ==========================================
@app.route('/api/emprestimos', methods=['GET', 'POST'])
def handle_emprestimos():
    if request.method == 'GET':
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM VW_LIVROS_EMPRESTADOS")
            return jsonify([serialize_row(r, cursor) for r in cursor.fetchall()])
            
    if request.method == 'POST':
        data = request.json
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("EXEC SP_REALIZAR_EMPRESTIMO @fk_aluno=?, @fk_exemplar=?, @data_prevista=?",
                               (data['fk_aluno'], data['fk_exemplar'], data['data_prevista_devolucao']))
                conn.commit()
            return jsonify({"message": "Empréstimo realizado!"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route('/api/emprestimos/<int:id>', methods=['PUT', 'DELETE'])
def update_emprestimo(id):
    if request.method == 'PUT':
        data = request.json
        with get_conn() as conn:
            cursor = conn.cursor()
            if data.get('status') == 'FINALIZADO' and data.get('data_devolucao'):
                cursor.execute("EXEC SP_DEVOLVER_LIVRO @id_emprestimo=?", (id,))
            else:
                cursor.execute("UPDATE EMPRESTIMO SET status=?, data_prevista_devolucao=? WHERE id_emprestimo=?",
                               (data['status'], data['data_prevista_devolucao'], id))
            conn.commit()
        return jsonify({"message": "Empréstimo atualizado!"})
    if request.method == 'DELETE':
        with get_conn() as conn:
            conn.execute("DELETE FROM EMPRESTIMO WHERE id_emprestimo=?", (id,)).commit()
        return jsonify({"message": "Excluído!"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)