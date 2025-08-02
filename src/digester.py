import base64
import os
from pathlib import Path
from typing import Union, Dict, Any, Optional
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from src.constants import MULTIMODAL_EXTRACTION_TEMPLATE, EXTRACTION_SCHEMA

class MultimodalInvoiceProcessor:
    """
    A comprehensive processor for extracting invoice data from images and PDF files
    using OpenAI's multimodal capabilities.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the processor with OpenAI client.
        
        Args:
            api_key: OpenAI API key (if None, uses environment variable OPENAI_API_KEY)
            model: OpenAI model to use for extraction
        """
        # Use provided API key or fall back to environment variable
        if api_key is None:
            api_key = os.getenv('OPENAI_API_KEY')
            
        if api_key is None:
            raise ValueError(
                "OpenAI API key must be provided either as parameter or "
                "through OPENAI_API_KEY environment variable"
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model
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
        return mime_types.get(extension, 'application/octet-stream')
    
    def _create_content_for_image(self, file_path: Union[str, Path], base64_data: str) -> list:
        """Create content structure for image files."""
        mime_type = self._get_mime_type(file_path)
        return [
            {"type": "text", "text": MULTIMODAL_EXTRACTION_TEMPLATE},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_data}"
                }
            }
        ]
    
    def _create_content_for_pdf(self, file_path: Union[str, Path], base64_data: str) -> list:
        """Create content structure for PDF files."""
        filename = Path(file_path).name
        return [
            {"type": "text", "text": MULTIMODAL_EXTRACTION_TEMPLATE},
            {
                "type": "file",
                "file": {
                    "filename": filename,
                    "file_data": f"data:application/pdf;base64,{base64_data}"
                }
            }
        ]
    
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
            content = self._create_content_for_image(file_path, base64_data)
        elif file_type == 'pdf':
            content = self._create_content_for_pdf(file_path, base64_data)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Make API call
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": content
                }],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "invoice_extraction_schema",
                        "schema": EXTRACTION_SCHEMA
                    }
                }
            )
            
            # Parse and return result
            result = json.loads(completion.choices[0].message.content)
            result['_metadata'] = {
                'file_path': str(file_path),
                'file_type': file_type,
                'model_used': self.model,
                'completion_tokens': completion.usage.completion_tokens,
                'prompt_tokens': completion.usage.prompt_tokens,
                'total_tokens': completion.usage.total_tokens
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
