OPENAI_MODEL = "gpt-4o"
MAX_WORKERS = 5

EXTRACTION_SCHEMA = {
    "title": "invoice",
    "description": "extracted invoice data",
    "type": "object",
    "properties": {
        "issuing_company_name": {
            "type": "string",
            "description": "The name of the company issuing the invoice"
        },
        "issuing_company_address": {
            "type": "string",
            "description": "The address of the company issuing the invoice"
        },
        "issuing_company_phone": {
            "type": "string",
            "description": "The phone number of the company issuing the invoice"
        },
        "issuing_company_website": {
            "type": "string",
            "description": "The website of the company issuing the invoice"
        },
        "issuing_company_email": {
            "type": "string",
            "description": "The email address of the company issuing the invoice"
        },
        "receiving_company_name": {
            "type": "string",
            "description": "The name of the company receiving the invoice"
        },
        "receiving_company_address": {
            "type": "string",
            "description": "The address of the company receiving the invoice"
        },
        "receiving_company_phone": {
            "type": "string",
            "description": "The phone number of the company receiving the invoice"
        },
        "receiving_company_website": {
            "type": "string",
            "description": "The website of the company receiving the invoice"
        },
        "receiving_company_email": {
            "type": "string",
            "description": "The email address of the company receiving the invoice"
        },
        "invoice_number": {
            "type": "string",
            "description": "The unique identifier for the invoice/bill"
        },
        "issue_date": {
            "type": "string",
            "description": "The date when the invoice was issued in YYYY-MM-DD format. Infer the date format from the invoice using the issuing company country if necessary",
        },
        "due_date": {
            "type": "string",
            "description": "The date when the invoice payment is due in YYYY-MM-DD format. Infer the date format from the invoice using the issuing company country if necessary",
        },
        "reference_number": {
            "type": "string",
            "description": "The reference number associated with the invoice"
        },
        "delivery_order_number": {
            "type": "string",
            "description": "The delivery order number associated with the invoice"
        },
        "currency": {
            "type": "string",
            "description": "The currency for all amounts in the invoice, if unspecified, assume SGD"
        },
        "line_items": {
            "type": "array",
            "description": "List of items/services in the invoice",
            "items": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "The name of the item or service"
                    },
                    "item_code": {
                        "type": "string",
                        "description": "The code or identifier for the item, sometimes called stock code"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the item or service"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "The quantity of the item"
                    },
                    "unit_price": {
                        "type": "number",
                        "description": "The price per unit of the item"
                    },
                    "amount": {
                        "type": "number",
                        "description": "The total amount for this line item (quantity × unit_price)"
                    }
                },
                "required": ["item_name", "quantity", "unit_price", "amount"]
            }
        },
        "gst_information": {
            "type": "object",
            "description": "Goods and services tax (GST) or other tax information for the invoice",
            "properties": {
                "gst_description": {
                    "type": "string",
                    "description": "Description of the GST/tax (e.g., 'GST 7%', 'VAT', etc.)"
                },
                "amount": {
                    "type": "number",
                    "description": "The GST/tax amount"
                }
            },
            "required": ["gst_description", "amount"]
        },
        "total_amount_due": {
            "type": "number",
            "description": "The total amount due including all taxes and charges"
        },
        "other_notes": {
            "type": "string",
            "description": "Any additional notes or comments related to the invoice"
        }
    },
    "required": ["invoice_number", "total_amount_due"],
}
