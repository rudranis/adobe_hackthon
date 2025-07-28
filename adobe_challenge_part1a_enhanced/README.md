# Adobe Connecting the Dots Challenge - Part 1A: PDF Outline Extractor

## Overview
This application extracts structured outlines (title, H1/H2/H3 headings with page numbers) from PDF documents and outputs them in a JSON format. It is designed to meet the requirements of Part 1A of Adobe's 'Connecting the Dots' Challenge.

## Requirements
- Docker compatible with AMD64 architecture.
- CPU-only execution.
- Model size (if any) ≤ 200MB.
- Processing time ≤ 10 seconds for a 50-page PDF.
- No internet access required during execution.

## Approach

### Libraries Used
- **PyMuPDF (Fitz):** A high-performance Python library for PDF processing. It allows efficient extraction of text, font information, and page details, which are crucial for identifying headings.

### Heading Detection Methodology
The application employs a heuristic-based approach for heading detection, primarily relying on font size analysis. The steps are as follows:
1.  **Text Extraction:** PyMuPDF is used to extract text blocks from each page, along with their associated font sizes and positions.
2.  **Font Size Analysis:** All unique font sizes present in the document are collected. The largest font sizes are then heuristically assigned as potential H1, H2, and H3 levels. A small epsilon is used for floating-point comparisons to account for minor variations in font rendering.
3.  **Hierarchical Assignment:** Text spans are classified as H1, H2, or H3 based on their font size relative to the determined thresholds. The logic ensures that H1 > H2 > H3 in terms of font size.
4.  **Page Number Association:** Each detected heading is associated with its corresponding page number.
5.  **Title Extraction:** The document title is first attempted to be extracted from the PDF's metadata. If not available or unreliable, a heuristic based on the largest font size on the first page is used as a fallback.

### Output Format
The output is a JSON file with the following structure:
```json
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
```

## How to Build and Run

### Build the Docker Image
```bash
docker build --platform linux/amd64 -t pdf-outline-extractor:latest .
```

### Run the Docker Container
This command will process all PDF files in the `./input` directory and save the generated JSON outlines to the `./output` directory.

First, create `input` and `output` directories in the same location as your `Dockerfile` and `app.py`:
```bash
mkdir input
mkdir output
```
Place your sample PDF files (e.g., `sample.pdf`) into the `input` directory.


### Ensure you're in the root directory where input/ and output/ folders exist, then run:

```powershell
Copy
Edit
docker run --rm `
  -v "${PWD}\input:/app/input" `
  -v "${PWD}\output:/app/output" `
  --network none `
  pdf-outline-extractor:latest
  ```

**Note:** The `app.py` currently expects a single input PDF and a single output JSON path as command-line arguments. The `CMD` in the Dockerfile will need to be updated to iterate through the `/app/input` directory and process each PDF. For now, this `README` assumes a single file processing for testing purposes, aligning with the challenge's `docker run` example which implies a single execution for a specific input/output. The final solution will need to adapt to the batch processing requirement.

## Future Improvements (for Part 1B)
-   **More Robust Heading Detection:** Incorporate machine learning models (within size constraints) or more advanced layout analysis for improved accuracy, especially for complex PDF structures.
-   **Semantic Understanding:** Beyond structural outlines, extract semantic relationships between sections for deeper insights.

