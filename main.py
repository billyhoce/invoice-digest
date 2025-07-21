from src.digester import digester
from src.constants import EXTRACTION_SCHEMA

if __name__ == "__main__":
    # Example usage of the digester class
    json_schema = EXTRACTION_SCHEMA
    
    document_path = "sample_invoice_1.png"
    
    my_digester = digester(json_schema=json_schema, model="gpt-4.1")
    result = my_digester.digest(document=document_path)
    
    print("Extracted Invoice Data:", result)