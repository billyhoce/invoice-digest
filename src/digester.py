from langchain.chat_models import init_chat_model
from typing import Dict, Any
from src.constants import EXTRACTION_TEMPLATE
from openai import RateLimitError
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel.pipeline_options import (
    VlmPipelineOptions,
)
from docling.datamodel import vlm_model_specs


class digester:
    def __init__(self, json_schema: Dict[str, Any], model: str = "gpt-4.1"):
        self.schema = json_schema
        self.init_converter()
        self.llm = init_chat_model(model)
        self.llm_structured_output = self.llm.with_structured_output(schema=json_schema)

    def init_converter(self):
        pipeline_options = VlmPipelineOptions(
            vlm_options=vlm_model_specs.SMOLDOCLING_MLX,  # <-- Choose the appropriate docling VLM model
        )

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                ),
            }
        )


    def digest(self, document: str):
        """
        Digests the given document and returns a structured representation.
        
        Args:
            document (str): The path of the document to digest.
        """
        invoice_text = self._convert_to_markdown(document)
        # Save the markdown text to a file for debugging purposes
        with open("markdown.txt", "w") as f:
            f.write(invoice_text)

        # Extract structured data from the document
        extracted_data = self._extract(invoice_text)
        return extracted_data
    

    def _convert_to_markdown(self, document: str) -> str:
        """
        Converts the document to markdown format.
        
        Args:
            document (str): The path of the document to convert.
        
        Returns:
            str: The markdown representation of the document.
        """
        return self.parser.convert(document).document.export_to_markdown()
    
    
    def _extract(self, invoice_text: str) -> Dict[str, Any]:
        """
        Extracts structured data from the document.
        
        Args:
            document (str): The path of the document to extract data from.
        
        Returns:
            Dict[str, Any]: The extracted structured data.
        """
        prompt = EXTRACTION_TEMPLATE.format(
            # schema=str(self.schema),
            invoice_text=invoice_text
        )
        try:
            extraction = self.llm_structured_output.invoke(prompt)
            return extraction
        except RateLimitError as e:
            print(f"Rate limit exceeded: {e}")
            return None