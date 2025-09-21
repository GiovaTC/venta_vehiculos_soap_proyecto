# db.py
import oracledb

# --- Configuración Oracle ---
DB_USER = "system"
DB_PASSWORD = "Tapiero123"
DB_DSN = "localhost:1521/orcl"  # Ajusta a tu entorno (SID/ServiceName)

pool = None

def init_pool():
    global pool
    if pool is None:
        pool = oracledb.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN,
            min=1,
            max=5,
            increment=1
        )
        print("✅ Pool de conexiones inicializado")
    return pool


def call_registrar_venta_xml(xml_text: str) -> str:
    global pool
    if pool is None:
        init_pool()

    conn = pool.acquire()
    try:
        cur = conn.cursor()
        result_var = cur.var(str)
        cur.execute(
            "BEGIN registrar_venta_xml(:p_xml, :p_result); END;",
            p_xml=xml_text,
            p_result=result_var
        )
        return result_var.getvalue()
    finally:
        pool.release(conn)
