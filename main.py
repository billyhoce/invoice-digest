import argparse
from dotenv import load_dotenv
from pathlib import Path
from src.digester import MultimodalInvoiceProcessor
from config import MODEL, MODEL_PROVIDER, MAX_WORKERS

def process_directory(input_dir: str = "INPUT_DOCUMENTS_HERE", output_dir: str = "OUTPUT_HERE"):
    """
    Process all supported files in input directory and save results to output directory.
    
    Args:
        input_dir: Directory containing invoice files to process
        output_dir: Directory to save extraction results
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(exist_ok=True)
    
    # Check if input directory exists
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return
    
    # Initialize the processor
    try:
        processor = MultimodalInvoiceProcessor(model=MODEL, model_provider=MODEL_PROVIDER)
        print(f"Initialized MultimodalInvoiceProcessor with model: {processor.model}")
    except Exception as e:
        print(f"Error initializing processor: {e}")
        return
    
    # Find all supported files in input directory
    supported_extensions = processor.supported_image_formats | processor.supported_pdf_formats
    files_to_process = []
    
    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            files_to_process.append(file_path)
    
    if not files_to_process:
        print(f"No supported files found in '{input_dir}'.")
        print(f"Supported formats: {', '.join(supported_extensions)}")
        return
    
    print(f"Found {len(files_to_process)} files to process:")
    for file_path in files_to_process:
        print(f"  - {file_path.name}")
    
    # Process each file and save results
    result = processor.extract_from_multiple_files(file_paths=files_to_process, max_workers=MAX_WORKERS)
    for file_path, data in result.items():
        file_path = Path(file_path)
        output_file = output_path / f"{file_path.stem}_extracted_{MODEL}_v1.json"
        processor.save_results(data, output_file)
        print(f"Saved extraction result for {file_path.name} to {output_file.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract invoice data from documents")
    parser.add_argument(
        "--input-dir", 
        default="INPUT_DOCUMENTS_HERE",
        help="Input directory containing invoice files (default: INPUT_DOCUMENTS_HERE)"
    )
    parser.add_argument(
        "--output-dir", 
        default="OUTPUT_HERE",
        help="Output directory for extraction results (default: OUTPUT_HERE)"
    )
    
    args = parser.parse_args()
    load_dotenv()
    process_directory(args.input_dir, args.output_dir)
