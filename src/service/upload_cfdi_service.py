from lxml import etree
from satcfdi.cfdi import CFDI
from prisma import Prisma
from fastapi import HTTPException
from datetime import datetime, timezone
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_cfdi(xml_bytes: bytes, user_id: str, db: Prisma):
    """Procesa un CFDI XML y lo guarda en la base de datos."""
    try:
        # Validar el XML con satcfdi
        logger.info("Validando el XML CFDI con satcfdi...")
        cfdi = CFDI.from_string(xml_bytes)
        logger.info("CFDI validado exitosamente con satcfdi.")
        logger.debug(f"Estructura del objeto CFDI: {dir(cfdi)}")

        # Parsear el XML con lxml para extraer datos
        logger.info("Iniciando parseo del XML con lxml...")
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(xml_bytes, parser=parser)
        logger.info("XML parseado exitosamente con lxml.")

        # Definir namespaces
        ns = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
            'pago20': 'http://www.sat.gob.mx/Pagos20',
            'nomina12': 'http://www.sat.gob.mx/nomina12'
        }

        # Extraer datos principales
        uuid = tree.xpath('//tfd:TimbreFiscalDigital/@UUID', namespaces=ns)
        if not uuid:
            raise ValueError("No se encontró el UUID en TimbreFiscalDigital")
        uuid = uuid[0]
        logger.debug(f"UUID extraído: {uuid}")

        version = tree.get('Version')
        serie = tree.get('Serie')
        folio = tree.get('Folio')
        issue_date = tree.get('Fecha')
        seal = tree.get('Sello')
        certificate_number = tree.get('NoCertificado')
        certificate = tree.get('Certificado')
        place_of_issue = tree.get('LugarExpedicion')
        type_ = tree.get('TipoDeComprobante')
        total = float(tree.get('Total', 0.0))
        subtotal = float(tree.get('SubTotal', 0.0))
        payment_method = tree.get('MetodoPago')
        payment_form = tree.get('FormaPago')
        currency = tree.get('Moneda')
        issuer_node = tree.find('cfdi:Emisor', namespaces=ns)
        receiver_node = tree.find('cfdi:Receptor', namespaces=ns)

        if issuer_node is None or receiver_node is None:
            raise ValueError("Emisor o Receptor no encontrados en el XML")

        issuer_rfc = issuer_node.get('Rfc')
        receiver_rfc = receiver_node.get('Rfc')
        cfdi_use = receiver_node.get('UsoCFDI')
        logger.debug(f"Datos extraídos - issuer_rfc: {issuer_rfc}, receiver_rfc: {receiver_rfc}, user_id: {user_id}")

        # Validar user_id
        if not isinstance(user_id, str) or len(user_id) != 13:
            logger.error(f"RFC de usuario inválido: {user_id}")
            raise HTTPException(status_code=400, detail=f"Invalid user RFC: {user_id}")

        # Convertir issue_date a formato ISO-8601 completo
        if issue_date:
            try:
                issue_date_dt = datetime.fromisoformat(issue_date.replace('Z', '+00:00') if issue_date.endswith('Z') else issue_date + 'Z')
                issue_date = issue_date_dt.isoformat()
                logger.debug(f"issue_date convertido: {issue_date}")
            except ValueError as e:
                logger.error(f"Invalid issue_date format: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid issue_date format: {str(e)}")

        # Verificar si el CFDI ya existe
        logger.info(f"Verificando si el CFDI con UUID {uuid} ya existe...")
        existing_cfdi = await db.cfdi.find_unique(where={'uuid': uuid})
        if existing_cfdi:
            raise HTTPException(status_code=400, detail="CFDI with this UUID already exists.")

        # Verificar que el usuario exista
        logger.debug(f"Verificando usuario con RFC {user_id}...")
        user = await db.user.find_unique(where={'rfc': user_id})
        if not user:
            logger.error(f"Usuario con RFC {user_id} no encontrado.")
            raise HTTPException(status_code=400, detail=f"User with RFC {user_id} not found.")

        # Manejar el Emisor (Issuer)
        logger.debug(f"Buscando/Creando emisor con RFC {issuer_rfc}...")
        issuer = await db.issuer.find_unique(where={'rfc_issuer': issuer_rfc})
        if not issuer:
            logger.debug(f"Creando nuevo emisor con RFC {issuer_rfc}...")
            issuer = await db.issuer.create(data={
                'rfc_issuer': issuer_rfc,
                'name_issuer': issuer_node.get('Nombre'),
                'tax_regime': issuer_node.get('RegimenFiscal'),
            })

        # Manejar el Receptor (Receiver)
        logger.debug(f"Buscando/Creando receptor con RFC {receiver_rfc}...")
        receiver = await db.receiver.find_first(where={'rfc_receiver': receiver_rfc})
        if not receiver:
            logger.debug(f"Creando nuevo receptor con RFC {receiver_rfc}...")
            receiver = await db.receiver.create(data={
                'rfc_receiver': receiver_rfc,
                'name_receiver': receiver_node.get('Nombre'),
                'cfdi_use': cfdi_use,
                'tax_regime': receiver_node.get('RegimenFiscalReceptor', None),
                'tax_address': receiver_node.get('DomicilioFiscalReceptor', None),
            })

        # Crear el registro CFDI
        logger.info("Creando registro CFDI en la base de datos...")
        cfdi_data = {
            'uuid': uuid,
            'version': version,
            'serie': serie,
            'folio': folio,
            'issue_date': issue_date,
            'seal': seal,
            'certificate_number': certificate_number,
            'certificate': certificate,
            'place_of_issue': place_of_issue,
            'type': type_,
            'total': total,
            'subtotal': subtotal,
            'payment_method': payment_method,
            'payment_form': payment_form,
            'currency': currency,
            'user_id': user_id,  # Campo directo obligatorio
            'issuer_id': issuer_rfc,  # Campo directo obligatorio
            'receiver_id': receiver.id if receiver else None,  # receiver_id es opcional
            'cfdi_use': cfdi_use,
            'export_status': None,  # Campo opcional
        }

        # Validar datos antes de crear
        required_fields = ['uuid', 'version', 'issue_date', 'type', 'total', 'subtotal', 'currency', 'user_id', 'issuer_id']
        for field in required_fields:
            if cfdi_data.get(field) is None:
                logger.error(f"Campo obligatorio faltante: {field}")
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        logger.debug(f"Datos para crear CFDI: {cfdi_data}")
        cfdi_record = await db.cfdi.create(data=cfdi_data)

        # Manejar Conceptos
        logger.debug("Procesando conceptos...")
        for concepto in tree.findall('cfdi:Conceptos/cfdi:Concepto', namespaces=ns):
            concept_record = await db.concept.create(data={
                'cfdi_id': cfdi_record.id,
                'fiscal_key': concepto.get('ClaveProdServ'),
                'description': concepto.get('Descripcion'),
                'quantity': float(concepto.get('Cantidad')),
                'unit_value': float(concepto.get('ValorUnitario')),
                'amount': float(concepto.get('Importe')),
                'discount': float(concepto.get('Descuento', 0.0)),
            })

            # Manejar Impuestos
            impuestos = concepto.find('cfdi:Impuestos', namespaces=ns)
            if impuestos is not None:
                for traslado in impuestos.findall('cfdi:Traslados/cfdi:Traslado', namespaces=ns):
                    await db.taxes.create(data={
                        'concept_id': concept_record.id,
                        'tax_type': 'traslado',
                        'rate': float(traslado.get('TasaOCuota')),
                        'amount': float(traslado.get('Importe')),
                    })
                for retencion in impuestos.findall('cfdi:Retenciones/cfdi:Retencion', namespaces=ns):
                    await db.taxes.create(data={
                        'concept_id': concept_record.id,
                        'tax_type': 'retencion',
                        'rate': float(retencion.get('TasaOCuota')),
                        'amount': float(retencion.get('Importe')),
                    })

        # Manejar CFDIs Relacionados
        logger.info("Procesando CFDIs relacionados...")
        cfdi_relacionados = tree.find('cfdi:CfdiRelacionados', namespaces=ns)
        if cfdi_relacionados is not None:
            for relacionado in cfdi_relacionados.findall('cfdi:CfdiRelacionado', namespaces=ns):
                await db.cfdirelation.create(data={
                    'cfdi_id': cfdi_record.id,
                    'related_uuid': relacionado.get('UUID'),
                    'relation_type': cfdi_relacionados.get('TipoRelacion'),
                })

        # Manejar Complementos (Pagos y Nómina)
        logger.debug("Procesando complementos...")
        if type_ == 'P':
            pago = tree.find('cfdi:Complemento/pago20:Pagos', namespaces=ns)
            if pago is not None:
                for p in pago.findall('pago20:Pago', namespaces=ns):
                    payment_date = p.get('FechaPago')
                    if payment_date:
                        try:
                            # Parsear y normalizar a UTC
                            payment_date_dt = datetime.fromisoformat(
                                payment_date.replace('Z', '+00:00') if payment_date.endswith('Z') else payment_date
                            )
                            # Forzar zona UTC e incluir milisegundos (opcional pero más seguro)
                            payment_date = payment_date_dt.astimezone(timezone.utc).isoformat(timespec='seconds')
                            logger.debug(f"payment_date convertido: {payment_date}")
                        except ValueError as e:
                            logger.error(f"Invalid payment_date format: {str(e)}")
                            raise HTTPException(status_code=400, detail=f"Invalid payment_date format: {str(e)}")
                    await db.paymentcomplement.create(data={
                        'cfdi_id': cfdi_record.id,
                        'payment_date': payment_date,
                        'payment_form': p.get('FormaDePagoP'),
                        'payment_currency': p.get('MonedaP'),
                        'payment_amount': float(p.get('Monto', 0.0)),
                    })

        if type_ == 'N':
            nomina = tree.find('cfdi:Complemento/nomina12:Nomina', namespaces=ns)
            if nomina is not None:
                logger.debug("Nómina encontrada, pero no implementada.")
                pass  # Implementar lógica para Nómina si es necesario

        logger.info("CFDI procesado y guardado exitosamente.")
        return cfdi_record

    except Exception as e:
        logger.error(f"Error al procesar el CFDI: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid CFDI XML: {str(e)}")