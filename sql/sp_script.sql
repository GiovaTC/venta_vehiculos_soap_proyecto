---------------------------------------------------------
-- Procedimiento almacenado
---------------------------------------------------------
CREATE OR REPLACE PROCEDURE registrar_venta_xml(
  p_xml    IN  CLOB,
  p_result OUT VARCHAR2
) AS
BEGIN
  -- Insertar CLIENTE
  MERGE INTO clientes c
  USING (
    SELECT x.id, x.nombre, x.documento, x.email, x.telefono
    FROM XMLTABLE(
      '/Venta/Cliente'
      PASSING XMLTYPE(p_xml)
      COLUMNS
        id        VARCHAR2(20)   PATH 'Id',
        nombre    VARCHAR2(100)  PATH 'Nombre',
        documento VARCHAR2(50)   PATH 'Documento',
        email     VARCHAR2(100)  PATH 'Email',
        telefono  VARCHAR2(20)   PATH 'Telefono'
    ) x
  ) data
  ON (c.id_cliente = data.id)
  WHEN MATCHED THEN
    UPDATE SET c.nombre = data.nombre,
               c.documento = data.documento,
               c.email = data.email,
               c.telefono = data.telefono
  WHEN NOT MATCHED THEN
    INSERT (id_cliente, nombre, documento, email, telefono)
    VALUES (data.id, data.nombre, data.documento, data.email, data.telefono);

  -- Insertar VEHICULO
  MERGE INTO vehiculos v
  USING (
    SELECT x.vin, x.marca, x.modelo, x.ano, x.precio
    FROM XMLTABLE(
      '/Venta/Vehiculo'
      PASSING XMLTYPE(p_xml)
      COLUMNS
        vin    VARCHAR2(50)   PATH 'Vin',
        marca  VARCHAR2(50)   PATH 'Marca',
        modelo VARCHAR2(50)   PATH 'Modelo',
        ano    NUMBER(4)      PATH 'Ano',
        precio NUMBER(12,2)   PATH 'Precio'
    ) x
  ) data
  ON (v.vin = data.vin)
  WHEN MATCHED THEN
    UPDATE SET v.marca = data.marca,
               v.modelo = data.modelo,
               v.ano = data.ano,
               v.precio = data.precio
  WHEN NOT MATCHED THEN
    INSERT (vin, marca, modelo, ano, precio)
    VALUES (data.vin, data.marca, data.modelo, data.ano, data.precio);

  -- Insertar COMPRAS
  INSERT INTO compras (id_cliente, vin, id_item, descripcion, cantidad, valor)
  SELECT c.id_cliente, v.vin, x.id_item, x.descripcion, x.cantidad, x.valor
  FROM XMLTABLE(
    '/Venta/Compras/Item'
    PASSING XMLTYPE(p_xml)
    COLUMNS
      id_item     VARCHAR2(20)   PATH 'IdItem',
      descripcion VARCHAR2(200)  PATH 'Descripcion',
      cantidad    NUMBER         PATH 'Cantidad',
      valor       NUMBER(12,2)   PATH 'Valor'
  ) x
  CROSS JOIN (
    SELECT id_cliente FROM XMLTABLE('/Venta/Cliente/Id' PASSING XMLTYPE(p_xml) COLUMNS id_cliente VARCHAR2(20) PATH '.') 
  ) c
  CROSS JOIN (
    SELECT vin FROM XMLTABLE('/Venta/Vehiculo/Vin' PASSING XMLTYPE(p_xml) COLUMNS vin VARCHAR2(50) PATH '.') 
  ) v;

  p_result := 'OK';

EXCEPTION
  WHEN OTHERS THEN
    p_result := 'ERROR: ' || SQLERRM;
END registrar_venta_xml;
/

COMMIT;