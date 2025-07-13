EXTRACTION_TEMPLATE = """
# Instructions
You are an expert in extracting information from documents.
Your task is to extract the information specified in the schema from the provided invoice document.
Return only the requested information in JSON format, without any additional text or explanation.

# Invoice Document:
{invoice_text}
"""