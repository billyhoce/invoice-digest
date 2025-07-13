from src.digester import digester

if __name__ == "__main__":
    # Example usage of the digester class
    json_schema = {
    "title": "invoice",
    "description": "extracted invoice data",
    "type": "object",
    "properties": {
        "invoice_number": {
            "type": "string",
            "description": "The unique identifier for the invoice",
        },
        "date": {
            "type": "string",
            "description": "The date of the invoice",
        },
        "total_amount": {
            "type": "integer",
            "description": "The total amount of the invoice"
        },
    },
    "required": ["invoice_number", "total_amount"],
}
    
    document_path = "sample_invoice_1.png"
    
    my_digester = digester(json_schema=json_schema, model="gpt-4.1")
    result = my_digester.digest(document=document_path)
    
    print("Extracted Invoice Data:", result)