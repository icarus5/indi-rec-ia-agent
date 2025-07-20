import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from azure.ai.documentintelligence import DocumentIntelligenceClient

from src.utils.logger import get_function_logger

logger = get_function_logger("function_app")

endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")


def analyze_invoice(
    url_source: dict, session_id: str = "", invoke_id: str = ""
) -> dict:
    """
    Analiza una factura usando Azure Document Intelligence y extrae su contenido.
    """
    try:
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=endpoint, credential=AzureKeyCredential(key)
        )

        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-invoice", AnalyzeDocumentRequest(url_source=url_source)
        )
        result = poller.result()
        invoice_summary = result.get("content", "")

        logger.info(
            f"Session ID: {session_id} - Invoke ID: {invoke_id} - Salida de Document Intelligence: {invoice_summary}"
        )

        return {"success": True, "ocr_context": invoice_summary}

    except Exception as e:
        logger.error(f"Error procesando la imagen para OCR enterprise: {e}")
        return {
            "success": False,
            "ocr_context": "Error al procesar la imagen, por favor intente de nuevo.",
        }


def analyze_receipt(
    url_source: dict, session_id: str = "", invoke_id: str = ""
) -> AnalyzeResult:
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-receipt", AnalyzeDocumentRequest(url_source=url_source)
    )
    receipts = poller.result()

    output_lines = []

    for receipt in receipts.documents:
        for item in receipt.fields.get("Items", {}).get("valueArray", []):
            obj = item.get("valueObject", {})
            description = obj.get("Description", {}).get("content", "")
            quantity = obj.get("Quantity", {}).get("content", "")
            total_price = obj.get("TotalPrice", {}).get("content", "")

            output_lines.append(
                f"{str(int(float(quantity)))} x {description} - Costo: {total_price} soles"
            )

        total = receipt.fields.get("Total", {}).get("content", "")
        output_lines.append(f"Monto Total: {total} soles")

    receipt_summary = "\n".join(output_lines)

    final_result = {"success": True, "message": receipt_summary, "ocr_context": ""}

    logger.info(
        f"Session ID: {session_id} - Invoke ID: {invoke_id} - Output Document Intelligence: {final_result}"
    )

    return final_result
