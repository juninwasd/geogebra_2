#!/usr/bin/env python3
"""Módulo simples para persistir cálculos/plots no Postgres.

Cria a tabela `calculations` (se não existir) e fornece funções para salvar
uma expressão, resultado e a imagem PNG do gráfico (armazenada como bytea).
Config por variáveis de ambiente ou valores padrão locais.
"""
import os
import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    'dbname': os.environ.get('GEOGEBRA_DB', 'geogebra'),
    'user': os.environ.get('GEOGEBRA_DB_USER', 'postgres'),
    'password': os.environ.get('GEOGEBRA_DB_PASS', 'senaisp'),
    'host': os.environ.get('GEOGEBRA_DB_HOST', 'localhost'),
    'port': os.environ.get('GEOGEBRA_DB_PORT', '5432'),
}


def get_pg_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        # caller should handle None
        print(f"[geodb] não foi possível conectar ao Postgres: {e}")
        return None


def init_db():
    conn = get_pg_connection()
    if conn is None:
        return False
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS calculations (
            id SERIAL PRIMARY KEY,
            expr TEXT,
            result TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            image BYTEA
            , user_id INTEGER
        );
        """
    )
    # users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()
    return True


def save_calculation(expr: str, result: str = None, image_bytes: bytes = None, user_id: int = None) -> bool:
    """Insere um registro na tabela calculations. Retorna True em sucesso."""
    conn = get_pg_connection()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO calculations (expr, result, image, user_id) VALUES (%s, %s, %s, %s)",
                (expr, result, psycopg2.Binary(image_bytes) if image_bytes is not None else None, user_id)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"[geodb] erro ao salvar cálculo: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_calculations(limit=50):
    conn = get_pg_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, expr, result, created_at, octet_length(image), user_id FROM calculations ORDER BY created_at DESC LIMIT %s", (limit,))
            rows = cur.fetchall()
        return rows
    except Exception as e:
        print(f"[geodb] erro ao listar: {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def create_user(username: str, password_hash: str) -> bool:
    conn = get_pg_connection()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING", (username, password_hash))
        conn.commit()
        return True
    except Exception as e:
        print(f"[geodb] erro ao criar usuário: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_user_by_username(username: str):
    conn = get_pg_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, password_hash, created_at FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
        return row
    except Exception as e:
        print(f"[geodb] erro get_user: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass
