import sqlite3
import os
from datetime import datetime


# =========================================================
# DATABASE LOCATION
# =========================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DB_NAME = os.path.join(
    PROJECT_ROOT,
    "backend",
    "certificates.db"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# CREATE / UPDATE DATABASE
# =========================================================

def init_database():

    conn = get_connection()

    cursor = conn.cursor()


    # =====================================================
    # CERTIFICATES TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificates (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_name TEXT NOT NULL,

            certificate_id TEXT NOT NULL,

            university TEXT NOT NULL,

            certificate_hash TEXT NOT NULL,

            created_at TEXT

        )
    """)


    # =====================================================
    # MIGRATION FOR OLD DATABASE
    # =====================================================

    cursor.execute(
        "PRAGMA table_info(certificates)"
    )

    columns = [
        column["name"]
        for column in cursor.fetchall()
    ]


    # -----------------------------------------------------
    # ADD created_at IF OLD DATABASE DOES NOT HAVE IT
    # -----------------------------------------------------

    if "created_at" not in columns:

        cursor.execute("""
            ALTER TABLE certificates
            ADD COLUMN created_at TEXT
        """)


    # -----------------------------------------------------
    # FILL created_at FOR OLD RECORDS
    # -----------------------------------------------------

    cursor.execute("""
        UPDATE certificates
        SET created_at = ?
        WHERE created_at IS NULL
    """, (
        datetime.now().isoformat(),
    ))


    # =====================================================
    # VERIFICATION HISTORY TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            certificate_id TEXT NOT NULL,

            uploaded_hash TEXT NOT NULL,

            database_match INTEGER NOT NULL,

            blockchain_match INTEGER NOT NULL,

            hash_match INTEGER NOT NULL,

            verification_status TEXT NOT NULL,

            verified_at TEXT NOT NULL

        )
    """)


    conn.commit()

    conn.close()


# =========================================================
# ADD OFFICIAL CERTIFICATE
# =========================================================

def add_certificate(
    student_name,
    certificate_id,
    university,
    certificate_hash
):

    conn = get_connection()

    cursor = conn.cursor()


    # -----------------------------------------------------
    # PREVENT DUPLICATE CERTIFICATE IDs
    # -----------------------------------------------------

    cursor.execute("""
        SELECT id

        FROM certificates

        WHERE certificate_id = ?

        LIMIT 1

    """, (
        certificate_id,
    ))


    existing = cursor.fetchone()


    if existing:

        conn.close()

        return False


    # -----------------------------------------------------
    # INSERT CERTIFICATE
    # -----------------------------------------------------

    try:

        cursor.execute("""
            INSERT INTO certificates
            (
                student_name,
                certificate_id,
                university,
                certificate_hash,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)

        """, (

            student_name,

            certificate_id,

            university,

            certificate_hash,

            datetime.now().isoformat()

        ))


        conn.commit()

        return True


    except sqlite3.Error:

        return False


    finally:

        conn.close()


# =========================================================
# FIND ONE CERTIFICATE
# =========================================================

def find_certificate(certificate_id):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT

            id,

            student_name,

            certificate_id,

            university,

            certificate_hash,

            created_at

        FROM certificates

        WHERE certificate_id = ?

        ORDER BY id ASC

        LIMIT 1

    """, (
        certificate_id,
    ))


    record = cursor.fetchone()

    conn.close()


    return record


# =========================================================
# GET ALL CERTIFICATES
# =========================================================

def get_all_certificates():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT

            id,

            student_name,

            certificate_id,

            university,

            certificate_hash,

            created_at

        FROM certificates

        ORDER BY id DESC
    """)


    records = cursor.fetchall()

    conn.close()


    return records


# =========================================================
# SAVE VERIFICATION
# =========================================================

def save_verification(

    certificate_id,

    uploaded_hash,

    database_match,

    blockchain_match,

    hash_match,

    verification_status

):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        INSERT INTO verification_history
        (
            certificate_id,
            uploaded_hash,
            database_match,
            blockchain_match,
            hash_match,
            verification_status,
            verified_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)

    """, (

        certificate_id,

        uploaded_hash,

        int(database_match),

        int(blockchain_match),

        int(hash_match),

        verification_status,

        datetime.now().isoformat()

    ))


    conn.commit()

    conn.close()


# =========================================================
# GET VERIFICATION HISTORY
# =========================================================

def get_verification_history():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT

            id,

            certificate_id,

            uploaded_hash,

            database_match,

            blockchain_match,

            hash_match,

            verification_status,

            verified_at

        FROM verification_history

        ORDER BY id DESC
    """)


    records = cursor.fetchall()

    conn.close()


    return records


# =========================================================
# INITIALIZE DATABASE
# =========================================================

init_database()