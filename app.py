# app.py
import sys
import types
import collections.abc
import http.cookies
import urllib.parse

# --- 🔹 Parche para Spyne en Python 3.12 ---
moves_module = types.ModuleType("spyne.util.six.moves")

collections_abc_module = types.ModuleType("spyne.util.six.moves.collections_abc")
collections_abc_module.MutableSet = collections.abc.MutableSet
collections_abc_module.Sequence = collections.abc.Sequence
collections_abc_module.Iterable = collections.abc.Iterable
collections_abc_module.Mapping = collections.abc.Mapping
collections_abc_module.Set = collections.abc.Set
collections_abc_module.KeysView = collections.abc.KeysView
collections_abc_module.ValuesView = collections.abc.ValuesView
collections_abc_module.ItemsView = collections.abc.ItemsView

http_cookies_module = types.ModuleType("spyne.util.six.moves.http_cookies")
http_cookies_module.SimpleCookie = http.cookies.SimpleCookie
http_cookies_module.Morsel = http.cookies.Morsel

urllib_parse_module = types.ModuleType("spyne.util.six.moves.urllib.parse")
urllib_parse_module.unquote = urllib.parse.unquote
urllib_parse_module.quote = urllib.parse.quote
urllib_parse_module.urlencode = urllib.parse.urlencode
urllib_parse_module.urlparse = urllib.parse.urlparse
urllib_parse_module.parse_qs = urllib.parse.parse_qs
urllib_parse_module.parse_qsl = urllib.parse.parse_qsl

sys.modules["spyne.util.six.moves"] = moves_module
sys.modules["spyne.util.six.moves.collections_abc"] = collections_abc_module
sys.modules["spyne.util.six.moves.http_cookies"] = http_cookies_module
sys.modules["spyne.util.six.moves.urllib.parse"] = urllib_parse_module
# --- 🔹 Fin del parche ---

from flask import Flask, request, Response
from spyne import Application, rpc, ServiceBase, Unicode, ComplexModel, Decimal
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from db import call_registrar_venta_xml, init_pool


# === 🔹 Modelos Spyne (coinciden con tu WSDL) ===
class ClienteType(ComplexModel):
    Id = Unicode
    Nombre = Unicode
    Documento = Unicode
    Email = Unicode
    Telefono = Unicode


class VehiculoType(ComplexModel):
    Placa = Unicode
    Marca = Unicode
    Modelo = Unicode
    Precio = Decimal


class RegistrarVentaResponseType(ComplexModel):
    Codigo = Unicode
    Mensaje = Unicode


# === 🔹 Servicio Spyne ===
class VentaService(ServiceBase):
    @rpc(ClienteType, VehiculoType, _returns=RegistrarVentaResponseType, _operation_name="RegistrarVenta")
    def RegistrarVenta(ctx, cliente, vehiculo):
        try:
            xml_text = f"""
            <RegistrarVentaRequest>
                <Cliente>
                    <Id>{cliente.Id}</Id>
                    <Nombre>{cliente.Nombre}</Nombre>
                    <Documento>{cliente.Documento}</Documento>
                    <Email>{cliente.Email}</Email>
                    <Telefono>{cliente.Telefono}</Telefono>
                </Cliente>
                <Vehiculo>
                    <Placa>{vehiculo.Placa}</Placa>
                    <Marca>{vehiculo.Marca}</Marca>
                    <Modelo>{vehiculo.Modelo}</Modelo>
                    <Precio>{vehiculo.Precio}</Precio>
                </Vehiculo>
            </RegistrarVentaRequest>
            """

            result = call_registrar_venta_xml(xml_text)

            return RegistrarVentaResponseType(
                Codigo="0",
                Mensaje=result
            )
        except Exception as e:
            return RegistrarVentaResponseType(
                Codigo="1",
                Mensaje=f"ERROR: {str(e)}"
            )


# --- Configuración Flask + Spyne ---
app = Flask(__name__)

soap_app = Application(
    [VentaService],
    tns="http://example.com/ventaVehiculos",
    name="VentaVehiculosService",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

wsgi_app = WsgiApplication(soap_app)


@app.route("/ventaVehiculos", methods=["POST"])
def soap_endpoint():
    environ = request.environ
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


# 🚨 Aquí forzamos el WSDL estático (idéntico al tuyo)
@app.route('/ventaVehiculos.wsdl', methods=['GET'])
def wsdl():
    wsdl_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions 
    xmlns="http://schemas.xmlsoap.org/wsdl/" 
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" 
    xmlns:tns="http://example.com/ventaVehiculos" 
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    targetNamespace="http://example.com/ventaVehiculos" 
    name="VentaVehiculosService">

  <types>
    <xsd:schema 
        targetNamespace="http://example.com/ventaVehiculos"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="http://example.com/ventaVehiculos"
        elementFormDefault="qualified"
        attributeFormDefault="unqualified">

      <xsd:element name="RegistrarVentaRequest" type="tns:RegistrarVentaRequestType"/>
      <xsd:element name="RegistrarVentaResponse" type="tns:RegistrarVentaResponseType"/>

      <xsd:complexType name="RegistrarVentaRequestType">
        <xsd:sequence>
          <xsd:element name="Cliente" type="tns:ClienteType"/>
          <xsd:element name="Vehiculo" type="tns:VehiculoType"/>
        </xsd:sequence>
      </xsd:complexType>

      <xsd:complexType name="RegistrarVentaResponseType">
        <xsd:sequence>
          <xsd:element name="Codigo" type="xsd:string"/>
          <xsd:element name="Mensaje" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>

      <xsd:complexType name="ClienteType">
        <xsd:sequence>
          <xsd:element name="Id" type="xsd:string"/>
          <xsd:element name="Nombre" type="xsd:string"/>
          <xsd:element name="Documento" type="xsd:string"/>
          <xsd:element name="Email" type="xsd:string"/>
          <xsd:element name="Telefono" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>

      <xsd:complexType name="VehiculoType">
        <xsd:sequence>
          <xsd:element name="Placa" type="xsd:string"/>
          <xsd:element name="Marca" type="xsd:string"/>
          <xsd:element name="Modelo" type="xsd:string"/>
          <xsd:element name="Precio" type="xsd:decimal"/>
        </xsd:sequence>
      </xsd:complexType>

    </xsd:schema>
  </types>

  <message name="RegistrarVentaRequestMessage">
    <part name="parameters" element="tns:RegistrarVentaRequest"/>
  </message>

  <message name="RegistrarVentaResponseMessage">
    <part name="parameters" element="tns:RegistrarVentaResponse"/>
  </message>

  <portType name="VentaVehiculosPortType">
    <operation name="RegistrarVenta">
      <input message="tns:RegistrarVentaRequestMessage"/>
      <output message="tns:RegistrarVentaResponseMessage"/>
    </operation>
  </portType>

  <binding name="VentaVehiculosBinding" type="tns:VentaVehiculosPortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="RegistrarVenta">
      <soap:operation soapAction="http://example.com/ventaVehiculos/RegistrarVenta"/>
      <input>
        <soap:body use="literal"/>
      </input>
      <output>
        <soap:body use="literal"/>
      </output>
    </operation>
  </binding>

  <service name="VentaVehiculosService">
    <port name="VentaVehiculosPort" binding="tns:VentaVehiculosBinding">
      <soap:address location="http://localhost:5000/ventaVehiculos"/>
    </port>
  </service>
</definitions>
"""
    return Response(wsdl_content, mimetype='text/xml')


if __name__ == "__main__":
    init_pool()
    print("✅ Pool de conexiones inicializado")
    print("🚀 Servicio corriendo en http://127.0.0.1:5000/ventaVehiculos")
    print("📄 WSDL disponible en http://127.0.0.1:5000/ventaVehiculos.wsdl")
    app.run(host="0.0.0.0", port=5000)
