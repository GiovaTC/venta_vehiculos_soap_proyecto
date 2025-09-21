def call_registrar_venta_xml(xml_text: str) -> str:
    if pool is None:
        init_pool()
    conn = pool.acquire()
    try:
        cur = conn.cursor()
        result_var = cur.var(str)
        cur.execute("BEGIN registrar_venta_xml(:p_xml, :p_result); END;",
                    p_xml=xml_text, p_result=result_var)
        return result_var.getvalue()
    finally:
        pool.release(conn)
    