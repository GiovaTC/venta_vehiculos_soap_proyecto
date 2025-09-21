class VentaService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def procesarXmlVenta(ctx, xml_text):
        if not xml_text or len(xml_text.strip()) == 0:
            return 'error: XML vacio'
        try:
            parsed = parse_venta_xml(xml_text)
        except Exception as e:
            return f'error_parse: {str(e)}'
        try:
            result = call_registrar_venta_xml(xml_text)
            return result
        except Exception as e:
            return f'error_db: {str(e)}'    