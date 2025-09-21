# app.py
import sys
import types
import collections.abc
import http.cookies
import urllib.parse

# --- 🔹 Parche para Spyne en Python 3.12 ---
# Crear módulo base: spyne.util.six.moves
moves_module = types.ModuleType("spyne.util.six.moves")

# Submódulo collections_abc
collections_abc_module = types.ModuleType("spyne.util.six.moves.collections_abc")
collections_abc_module.MutableSet = collections.abc.MutableSet
collections_abc_module.Sequence = collections.abc.Sequence
collections_abc_module.Iterable = collections.abc.Iterable
collections_abc_module.Mapping = collections.abc.Mapping
collections_abc_module.Set = collections.abc.Set
collections_abc_module.KeysView = collections.abc.KeysView
collections_abc_module.ValuesView = collections.abc.ValuesView
collections_abc_module.ItemsView = collections.abc.ItemsView

# Submódulo http_cookies
http_cookies_module = types.ModuleType("spyne.util.six.moves.http_cookies")
http_cookies_module.SimpleCookie = http.cookies.SimpleCookie
http_cookies_module.Morsel = http.cookies.Morsel

# Submódulo urllib.parse
urllib_parse_module = types.ModuleType("spyne.util.six.moves.urllib.parse")
urllib_parse_module.unquote = urllib.parse.unquote
urllib_parse_module.quote = urllib.parse.quote
urllib_parse_module.urlencode = urllib.parse.urlencode
urllib_parse_module.urlparse = urllib.parse.urlparse
urllib_parse_module.parse_qs = urllib.parse.parse_qs
urllib_parse_module.parse_qsl = urllib.parse.parse_qsl

# Registrar en sys.modules
sys.modules["spyne.util.six.moves"] = moves_module
sys.modules["spyne.util.six.moves.collections_abc"] = collections_abc_module
sys.modules["spyne.util.six.moves.http_cookies"] = http_cookies_module
sys.modules["spyne.util.six.moves.urllib.parse"] = urllib_parse_module
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

@app.route("/ventaVehiculos", methods=["POST"])
def soap_endpoint():
    # Spyne necesita trabajar a nivel WSGI
    environ = request.environ
    # start_response: función que Spyne invoca para setear headers y status
    headers_status = {}

    def start_response(status, response_headers, exc_info=None):
        headers_status['status'] = status
        headers_status['headers'] = response_headers
        return None

    result = wsgi_app(environ, start_response)

    status_code = int(headers_status['status'].split(' ')[0])
    headers = headers_status['headers']
    body = b"".join(result)

    return Response(body, status=status_code, headers=dict(headers))

if __name__ == "__main__":
    init_pool()
    app.run(host="0.0.0.0", port=5000)
