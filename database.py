import sqlite3
from contextlib import contextmanager

# Configurações
DATABASE_PATH = "reservas.db"
ADMIN_EMAIL = "admin@localhotel.com"
ADMIN_PASSWORD = "admin123"

@contextmanager
def get_db_connection():
    """Conecta ao banco de dados SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Tabela de Espaços (Quartos, Salas, Auditórios)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS espacos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('quarto', 'sala', 'auditório')),
                capacidade INTEGER NOT NULL,
                descricao TEXT,
                status INTEGER DEFAULT 1,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de Usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                telefone TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de Reservas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_espaco INTEGER NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                hora_inicio TEXT,
                hora_fim TEXT,
                participantes INTEGER NOT NULL,
                status INTEGER DEFAULT 1,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(id_espaco) REFERENCES espacos(id)
            )
        ''')

        # Criar índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reserva_data ON reservas(data_inicio, data_fim)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reserva_status ON reservas(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_espaco_status ON espacos(status)')

        # Criar admin padrão se não existir
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (ADMIN_EMAIL,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO usuarios (email, senha, telefone, nome) VALUES (?, ?, ?, ?)",
                (ADMIN_EMAIL, ADMIN_PASSWORD, "", "Admin do Sistema")
            )

        conn.commit()
        print("Banco de dados iniciado com sucesso!")

# ─── ESPAÇOS ────────────────────────────────────────────────────────────────

def get_espacos():
    """Retorna todos os espaços cadastrados."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM espacos ORDER BY nome")
        return [dict(row) for row in cursor.fetchall()]

def criar_espaco(nome, tipo, capacidade, descricao=""):
    """Cria um novo espaço e retorna o id gerado."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO espacos (nome, tipo, capacidade, descricao) VALUES (?, ?, ?, ?)",
            (nome, tipo, capacidade, descricao)
        )
        return cursor.lastrowid

def editar_espaco(espaco_id, nome, tipo, capacidade, descricao=""):
    """Atualiza um espaço existente. Retorna o número de linhas afetadas."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE espacos SET nome=?, tipo=?, capacidade=?, descricao=? WHERE id=?",
            (nome, tipo, capacidade, descricao, espaco_id)
        )
        return cursor.rowcount

def remover_espaco(espaco_id):
    """Remove um espaço pelo id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM espacos WHERE id=?", (espaco_id,))
        return cursor.rowcount

# ─── RESERVAS ───────────────────────────────────────────────────────────────

def get_reservas():
    """Retorna todas as reservas cadastradas."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reservas ORDER BY data_inicio")
        return [dict(row) for row in cursor.fetchall()]

def criar_reserva(id_espaco, data_inicio, data_fim, participantes,
                  hora_inicio=None, hora_fim=None):
    """Cria uma nova reserva e retorna o id gerado."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO reservas
               (id_espaco, data_inicio, data_fim, hora_inicio, hora_fim, participantes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (id_espaco, str(data_inicio), str(data_fim), hora_inicio, hora_fim, participantes)
        )
        return cursor.lastrowid

def remover_reserva(reserva_id):
    """Cancela/remove uma reserva pelo id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reservas WHERE id=?", (reserva_id,))
        return cursor.rowcount

def verificar_disponibilidade(espaco_id, data_inicio, data_fim):
    """
    Retorna True se o espaço estiver disponível no período informado,
    False se houver conflito com outra reserva ativa.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT COUNT(*) FROM reservas
               WHERE id_espaco = ?
                 AND status = 1
                 AND data_inicio <= ?
                 AND data_fim >= ?""",
            (espaco_id, str(data_fim), str(data_inicio))
        )
        count = cursor.fetchone()[0]
        return count == 0
