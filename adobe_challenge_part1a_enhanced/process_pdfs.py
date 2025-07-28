#!/usr/bin/env python3
"""
Batch processing script for PDF outline extraction.
Processes all PDF files in /app/input and generates corresponding JSON files in /app/output.
Optimized for the Adobe Challenge requirements.
"""

import os
import sys
import time
import json
import signal
from pathlib import Path
from app import extract_outline

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def timeout_handler(signum, frame):
    """Handle timeout signal"""
    raise TimeoutError("PDF processing timeout exceeded")

def setup_timeout(seconds):
    """Setup processing timeout"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def clear_timeout():
    """Clear processing timeout"""
    signal.alarm(0)

def validate_directories():
    """Validate input and output directories"""
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Create output directory if it doesn\\'t exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if input directory exists
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        sys.exit(1)
    
    return input_dir, output_dir

def find_pdf_files(input_dir):
    """Find all PDF files in input directory"""
    pdf_files = []
    for file_path in input_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".pdf":
            pdf_files.append(file_path)
    
    return sorted(pdf_files)  # Sort for consistent processing order

def estimate_pages(pdf_path):
    """Quickly estimate number of pages for timeout calculation"""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        doc.close()
        return page_count
    except Exception:
        return 50  # Assume max pages if can\\'t determine

def calculate_timeout(page_count):
    """Calculate appropriate timeout based on page count"""
    # Base: 10 seconds for 50 pages as per requirements
    # Add buffer for complex documents
    base_timeout = max(10, (page_count / 50) * 10)
    return min(base_timeout * 1.5, 30)  # Cap at 30 seconds with 50% buffer

def process_single_pdf(pdf_path, output_path, timeout_seconds=15):
    """Process a single PDF with timeout protection"""
    start_time = time.time()
    result = None
    error_msg = None
    
    try:
        # Set up timeout protection
        setup_timeout(int(timeout_seconds))
        
        print(f"Processing {pdf_path.name}...", end=" ", flush=True)
        
        # Extract outline
        result = extract_outline(str(pdf_path))
        
        # Clear timeout
        clear_timeout()
        
        # Validate result structure
        if not isinstance(result, dict) or "title" not in result or "outline" not in result:
            raise ValueError("Invalid result structure")
        
        # Ensure outline is a list
        if not isinstance(result["outline"], list):
            result["outline"] = []
        
        # Save result to JSON file with proper error handling
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        processing_time = time.time() - start_time
        print(f"✓ Success ({processing_time:.2f}s)")
        
        # Warn if processing time is concerning
        if processing_time > 10:
            print(f"  Warning: Processing took {processing_time:.2f}s (>10s target)")
        
        return True, processing_time, None
        
    except TimeoutError:
        clear_timeout()
        processing_time = time.time() - start_time
        error_msg = f"Timeout after {processing_time:.1f}s"
        print(f"✗ {error_msg}")
        
    except Exception as e:
        clear_timeout()
        processing_time = time.time() - start_time
        error_msg = str(e)
        print(f"✗ Error: {error_msg} ({processing_time:.2f}s)")
    
    # Create error result file
    try:
        error_result = {
            "title": "",
            "outline": [],
            "error": error_msg,
            "processing_time": processing_time
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(error_result, f, indent=2, ensure_ascii=False)
    except Exception as save_error:
        print(f"  Additional error saving error result: {save_error}")
    
    return False, processing_time, error_msg

def print_summary(results):
    """Print processing summary"""
    total_files = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total_files - successful
    total_time = sum(r["processing_time"] for r in results)
    avg_time = total_time / total_files if total_files > 0 else 0
    
    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    print(f"Total files:     {total_files}")
    print(f"Successful:      {successful}")
    print(f"Failed:          {failed}")
    print(f"Success rate:    {(successful/total_files*100):.1f}%" if total_files > 0 else "N/A")
    print(f"Total time:      {total_time:.2f}s")
    print(f"Average time:    {avg_time:.2f}s per file")
    print("="*50)
    
    # Show failed files if any
    if failed > 0:
        print(f"\nFAILED FILES:")
        for result in results:
            if not result["success"]:
                print(f"  • {result['filename']}: {result['error']}")

def validate_environment():
    """Validate the runtime environment"""
    try:
        import fitz
        print(f"PyMuPDF version: {fitz.version[0]}")
    except ImportError:
        print("Error: PyMuPDF not installed")
        sys.exit(1)
    
    # Check available memory (basic check)
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"Available memory: {memory.available // (1024**3):.1f}GB")
    except ImportError:
        pass  # psutil not required, just nice to have

def main():
    """Main processing function"""
    print("Adobe Challenge - PDF Outline Extractor")
    print("Processing all PDFs in /app/input directory")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Validate environment
    validate_environment()
    
    # Validate and setup directories
    input_dir, output_dir = validate_directories()
    
    # Find PDF files
    pdf_files = find_pdf_files(input_dir)
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        print("This is not an error - exiting gracefully")
        return 0
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    print("-" * 50)
    
    # Process each PDF
    results = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        # Generate output filename
        output_filename = pdf_path.stem + ".json"
        output_path = output_dir / output_filename
        
        print(f"[{i}/{len(pdf_files)}] ", end="")
        
        # Estimate timeout based on file size and pages
        try:
            page_count = estimate_pages(pdf_path)
            timeout_seconds = calculate_timeout(page_count)
            print(f"({page_count} pages, {timeout_seconds:.0f}s timeout) ", end="")
        except Exception:
            timeout_seconds = 15
            print("(timeout: 15s) ", end="")
        
        # Process the PDF
        success, processing_time, error_msg = process_single_pdf(
            pdf_path, output_path, timeout_seconds
        )
        
        # Record result
        results.append({
            "filename": pdf_path.name,
            "success": success,
            "processing_time": processing_time,
            "error": error_msg,
            "output_file": output_filename
        })
        
        # Add small delay between files to prevent resource exhaustion
        if i < len(pdf_files):  # Don\\'t delay after last file
            time.sleep(0.1)
    
    # Print summary
    print_summary(results)
    
    # Return appropriate exit code
    failed_count = sum(1 for r in results if not r["success"])
    if failed_count == len(results):
        print("\nAll files failed - check your PDFs and dependencies")
        return 1
    elif failed_count > 0:
        print(f"\n{failed_count} files failed - partial success")
        return 0  # Don\\'t fail the container for partial failures
    else:
        print("\nAll files processed successfully!")
        return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)


