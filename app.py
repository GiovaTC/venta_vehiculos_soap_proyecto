# app.py
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
    