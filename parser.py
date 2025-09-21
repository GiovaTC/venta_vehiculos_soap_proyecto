def parse_venta_xml(xml_text: str) -> dict:
    root = etree.fromstring(xml_text.encode('utf-8'))

    cliente = {
        'id': _get_text(root, './Cliente/Id'),
        'nombre': _get_text(root, './Cliente/Nombre'),
        'documento': _get_text(root, '.Cliente/Documento'),
        'email': _get_text(root, './Cliente/Email'),
        'telefono': _get_text(root, './Cliente/Telefono'),
    }

    vehiculo = {
        'vin': _get_text(root, './Vehiculo/Vin'),
        'marca': _get_text(root, './Vehiculo/Marca'),
        'modelo': _get_text(root, './Vehiculo/Modelo'),
        'ano': _get_text(root, './Vehiculo/Ano'),
        'precio': _get_text(root, './Vehiculo/Precio'),
    }

    items = []
    for item in  root.xpath('./Compras/Item'):
        items.append({
            'id': _get_text(item, './IdItem'),
            'desc': _get_text(item, './Descripcion'),
            'cantidad': _get_text(item, './Cantidad'),
            'valor': _get_text(item, './Valor'),
        })
    
    return {'cliente': cliente, 'vehiculo': vehiculo, 'items': items}