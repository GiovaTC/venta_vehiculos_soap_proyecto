# app.py
import sys
import types

# --- 🔹 Parche para Spyne en Python 3.12 ---
import sys
import types
import collections.abc

module_name = "spyne.util.six.moves.collections_abc"
fake_module = types.ModuleType(module_name)

# Mapear clases necesarias
fake_module.MutableSet = collections.abc.MutableSet
fake_module.Sequence = collections.abc.Sequence
fake_module.Iterable = collections.abc.Iterable  # 🔹 agregado

sys.modules[module_name] = fake_module
# --- 🔹 Fin del parche ---

from flask import Flask, request, Response
from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from db import call_registrar_venta_xml, init_pool
from parser import parse_venta_xml


class VentaService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def procesarXmlVenta(ctx, xml_text):
        if not xml_text or len(xml_text.strip()) == 0:
            return 'ERROR: XML vacío'
        try:
            parsed = parse_venta_xml(xml_text)
        except Exception as e:
            return f'ERROR_PARSE: {str(e)}'
        try:
            result = call_registrar_venta_xml(xml_text)
            return result
        except Exception as e:
            return f'ERROR_DB: {str(e)}'


# --- Configuración Flask + Spyne ---
app = Flask(__name__)

soap_app = Application(
    [VentaService],
    tns="venta.vehiculos.soap",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(soap_app)


@app.route("/soap", methods=["POST"])
def soap_endpoint():
    response = Response()
    response.status_code = 200
    response.headers["Content-Type"] = "text/xml"
    response.data = wsgi_app(request.environ, response.start_response)
    return response


if __name__ == "__main__":
    init_pool()
    app.run(host="0.0.0.0", port=5000)
