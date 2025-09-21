from flask import Flask, request, Response, send_from_directory
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Decimal, Date
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import oracledb
import os

# ==============================
# Configuración Flask
# ==============================
app = Flask(__name__)

# ==============================
# Configuración de Oracle (Pool)
# ==============================
pool = None

def init_pool():
    global pool
    if pool is None:
        pool = oracledb.create_pool(
            user="USUARIO",
            password="PASSWORD",
            dsn="localhost/XEPDB1",
            min=1,
            max=5,
            increment=1
        )
        print("✅ Pool de conexiones inicializado")

# ==============================
# Servicio SOAP
# ==============================
class VentaVehiculosService(ServiceBase):

    @rpc(Integer, Unicode, Unicode, Integer, Unicode, Unicode, Date, Decimal, _returns=Unicode)
    def RegistrarVenta(ctx, ClienteId, ClienteNombre, ClienteEmail,
                       VehiculoId, VehiculoMarca, VehiculoModelo,
                       CompraFecha, CompraMonto):
        """Registra una venta en la base de datos Oracle"""
        if pool is None:
            init_pool()

        try:
            conn = pool.acquire()
            cur = conn.cursor()

            result_var = cur.var(str)
            cur.execute("""
                BEGIN
                    registrar_venta(:p_cliente_id, :p_cliente_nombre, :p_cliente_email,
                                    :p_vehiculo_id, :p_vehiculo_marca, :p_vehiculo_modelo,
                                    :p_compra_fecha, :p_compra_monto, :p_resultado);
                END;
                """,
                p_cliente_id=ClienteId,
                p_cliente_nombre=ClienteNombre,
                p_cliente_email=ClienteEmail,
                p_vehiculo_id=VehiculoId,
                p_vehiculo_marca=VehiculoMarca,
                p_vehiculo_modelo=VehiculoModelo,
                p_compra_fecha=CompraFecha,
                p_compra_monto=CompraMonto,
                p_resultado=result_var
            )

            resultado = result_var.getvalue()
            conn.commit()
            return f"✅ Venta registrada correctamente: {resultado}"

        except Exception as e:
            return f"❌ Error registrando venta: {str(e)}"

        finally:
            if conn:
                conn.close()

# ==============================
# Configuración de la aplicación SOAP
# ==============================
soap_app = Application(
    [VentaVehiculosService],
    tns='http://example.com/ventaVehiculos',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

soap_wsgi_app = WsgiApplication(soap_app)

@app.route('/ventaVehiculos', methods=['POST'])
def soap_service():
    """ Endpoint SOAP """
    response = Response()
    response.status_code = 200
    response.headers['Content-Type'] = 'text/xml; charset=utf-8'
    response.set_data(soap_wsgi_app(request.environ, response.start_response))
    return response

# ==============================
# Endpoint WSDL estático (desde carpeta xml)
# ==============================
@app.route('/ventaVehiculos.wsdl', methods=['GET'])
def wsdl():
    """ Sirve el archivo WSDL desde carpeta xml """
    wsdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xml")
    return send_from_directory(wsdl_dir, "ventaVehiculos.wsdl", mimetype="text/xml")

# ==============================
# Main
# ==============================
if __name__ == '__main__':
    init_pool()
    print("🚀 Servicio corriendo en http://127.0.0.1:5000/ventaVehiculos")
    print("📄 WSDL disponible en http://127.0.0.1:5000/ventaVehiculos.wsdl")
    app.run(host="0.0.0.0", port=5000)
