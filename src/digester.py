import base64
from pathlib import Path
from typing import Union, Dict, Any
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.constants import MULTIMODAL_EXTRACTION_TEMPLATE
from config import EXTRACTION_SCHEMA
from langchain.chat_models import init_chat_model

class MultimodalInvoiceProcessor:
    """
    A comprehensive processor for extracting invoice data from images and PDF files
    using OpenAI's multimodal capabilities.
    """

    def __init__(self, model: str = "gpt-4o", model_provider: str = None):
        """
        Initialize the processor with provided model
        
        Args:
            api_key: OpenAI API key (if None, uses environment variable OPENAI_API_KEY)
            model: OpenAI model to use for extraction
        """
        self.model = model
        self.llm = init_chat_model(model=model, model_provider=model_provider)
        self.llm_structured_output = self.llm.with_structured_output(EXTRACTION_SCHEMA, include_raw=True)
        self.supported_image_formats = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        self.supported_pdf_formats = {'.pdf'}
    
    def _get_file_type(self, file_path: Union[str, Path]) -> str:
        """Determine file type based on extension."""
        extension = Path(file_path).suffix.lower()
        if extension in self.supported_image_formats:
            return 'image'
        elif extension in self.supported_pdf_formats:
            return 'pdf'
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def _encode_file_to_base64(self, file_path: Union[str, Path]) -> str:
        """Encode file to base64 string."""
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")
    
    def _get_mime_type(self, file_path: Union[str, Path]) -> str:
        """Get MIME type for the file."""
        extension = Path(file_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf'
        }
        return mime_types.get(extension)
    
    def _create_content_for_image(self, file_path: Union[str, Path], base64_data: str) -> Dict[str, Any]:
        """Create content structure for image files."""
        mime_type = self._get_mime_type(file_path)
        return {
            "type": "image",
            "source_type": "base64",
            "data": base64_data,
            "mime_type": mime_type,
        }

    def _create_content_for_pdf(self, file_path: Union[str, Path], base64_data: str) -> Dict[str, Any]:
        """Create content structure for PDF files."""
        mime_type = self._get_mime_type(file_path)
        file_name = Path(file_path).name
        return {
            "type": "file",
            "source_type": "base64",
            "mime_type": mime_type,
            "data": base64_data,
            "filename": file_name
        }
    
    def extract_invoice_data(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract invoice data from an image or PDF file.
        
        Args:
            file_path: Path to the invoice file (image or PDF)
            
        Returns:
            Dictionary containing extracted invoice data
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type and create appropriate content
        file_type = self._get_file_type(file_path)
        base64_data = self._encode_file_to_base64(file_path)
        
        if file_type == 'image':
            invoice_content = self._create_content_for_image(file_path, base64_data)
        elif file_type == 'pdf':
            invoice_content = self._create_content_for_pdf(file_path, base64_data)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Make API call
        try:
            message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": MULTIMODAL_EXTRACTION_TEMPLATE,
                    },
                    invoice_content
                ],
            }
            response = self.llm_structured_output.invoke([message])
            
            # Parse and return result
            result = response['parsed']
            result['_metadata'] = {
                'file_path': str(file_path),
                'file_type': file_type,
                'model_used': self.model,
                'total_tokens': response['raw'].usage_metadata['total_tokens'],
                'input_tokens': response['raw'].usage_metadata['input_tokens'],
                'output_tokens': response['raw'].usage_metadata['output_tokens']
            }
            return result
            
        except Exception as e:
            raise RuntimeError(f"Error during API call: {str(e)}")

    def extract_from_multiple_files(self, file_paths: list, max_workers: int = 3) -> Dict[str, Dict[str, Any]]:
        """
        Extract invoice data from multiple files concurrently using ThreadPoolExecutor.
        
        Args:
            file_paths: List of file paths to process
            max_workers: Maximum number of concurrent threads (default: 3 to respect API limits)
            
        Returns:
            Dictionary with file paths as keys and extraction results as values
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks - more explicit version
            future_to_file = {}
            for file_path in file_paths:
                future = executor.submit(self._extract_single_file_safe, file_path)
                future_to_file[future] = file_path
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results[str(file_path)] = result
                    print(f"✓ Completed: {Path(file_path).name}")
                except Exception as e:
                    results[str(file_path)] = {
                        'error': str(e),
                        '_metadata': {
                            'file_path': str(file_path),
                            'status': 'failed'
                        }
                    }
                    print(f"✗ Failed: {Path(file_path).name} - {str(e)}")
        
        return results
    
    def _extract_single_file_safe(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Safe wrapper for extract_invoice_data that handles exceptions gracefully.
        Used by concurrent processing.
        """
        try:
            return self.extract_invoice_data(file_path)
        except Exception as e:
            raise RuntimeError(f"Error processing {file_path}: {str(e)}")

    def batch_extract_invoice_data(self, file_paths: list, output_dir: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract invoice data in batch from multiple files using openAI's batch processing API.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary with file paths as keys and extraction results as values
        """
        # TODO: Implement batch processing logic
        return
    
    def save_results(self, results: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """Save extraction results to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
