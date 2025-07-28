import fitz  # PyMuPDF
import json
import re
import nltk
from collections import Counter
from config import (
    HEADING_FONT_SIZE_THRESHOLDS,
    HEADING_KEYWORDS,
    DEFAULT_CONFIG
)

# Download required NLTK data (only if not already present)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

def is_bold(span):
    return (span["flags"] & 1) > 0

def is_italic(span):
    return (span["flags"] & 2) > 0

def is_likely_heading(text, config, font_size, dominant_font_size, is_bold_text, page_height, is_title_candidate=False):
    """
    Enhanced semantic analysis to determine if text is likely a heading.
    Uses multiple heuristics including:
    - Length constraints
    - Capitalization patterns
    - Common heading keywords
    - Sentence structure
    - Specific numbering patterns (e.g., 1.1, 1.1.1)
    - Relative font size and boldness
    - Position on page (for title candidates)
    """
    text = text.strip()
    if not text or len(text) < config["min_heading_chars"]:
        return False
    
    if len(text) > config["max_heading_chars"]:
        return False
    
    # Filter out common non-heading patterns early
    if any(re.match(pattern, text, re.IGNORECASE) for pattern in config["ignore_patterns"]):
        return False

    # Check for common heading patterns (more specific and ordered by likelihood)
    heading_patterns = [
        r"^\d+(\.\d+)*\s+[A-Z]",  # Numbered sections like "1. Introduction" or "1.1.1 Sub-section"
        r"^(Chapter|Section|Part|Assignment|Exercise|Lab|Practical|Experiment)\s+\d+\b",
        r"^(Introduction|Conclusion|Summary|Overview|Background|Methodology|Results|Discussion|Aim|Theory|Problem statement|Assignment No)",
    ]
    
    for pattern in heading_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # Title-specific patterns (more lenient for title page)
    if is_title_candidate:
        if text.isupper() and len(text.split()) <= 5: # Short all-caps phrases
            return True
        if re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$", text) and len(text.split()) <= 7: # Title case
            return True

    # General heading patterns
    # All caps text (e.g., "THIRD YEAR", "LABORATORY MANUAL") - more strict for general headings
    if text.isupper() and len(text.split()) <= 4 and len(text) > 5:
        return True

    # Title case (e.g., "Human Computer Interaction") - more strict for general headings
    words = text.split()
    if 1 <= len(words) <= 6 and all(word[0].isupper() if word else False for word in words) and not text.isupper():
        return True

    # Keyword-based semantic scoring (more targeted)
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words("english"))
    filtered_tokens = [w for w in tokens if not w in stop_words and w.isalpha()]

    for level, keywords in HEADING_KEYWORDS.items():
        if any(keyword in filtered_tokens for keyword in keywords):
            return True
    
    # Consider relative font size and boldness as a strong indicator
    if dominant_font_size > 0 and font_size > dominant_font_size * 1.2 and is_bold_text:
        return True

    return False

def extract_outline(pdf_path, config=None):
    doc = fitz.open(pdf_path)
    outline = []
    title = ""

    # Merge default_config with external config values
    current_config = DEFAULT_CONFIG.copy()
    if config:
        current_config.update(config)
    
    # Use HEADING_FONT_SIZE_THRESHOLDS from config.py
    h_thresholds = HEADING_FONT_SIZE_THRESHOLDS

    # Calculate dominant font size for each page
    page_dominant_font_sizes = {}
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        font_sizes = []
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(span["size"])
        if font_sizes:
            page_dominant_font_sizes[page_num] = Counter(font_sizes).most_common(1)[0][0]
        else:
            page_dominant_font_sizes[page_num] = 0

    # 1. Enhanced Title Extraction
    # Try metadata first, then multi-page heuristic analysis
    if doc.metadata and doc.metadata.get("title") and doc.metadata.get("title").strip() not in ["gdsgsdfg", ""]:
        title = doc.metadata.get("title").strip()

    if not title:
        # Analyze first few pages for a prominent title
        title_candidates = []
        
        for page_num in range(min(current_config["title_search_pages"], len(doc))): # Check first few pages
            page = doc.load_page(page_num)
            text_blocks = page.get_text("dict")["blocks"]
            page_height = page.rect.height
            page_width = page.rect.width

            for block in text_blocks:
                if "lines" in block: 
                    for line in block["lines"]:
                        for span in line["spans"]:
                            font_size = span["size"]
                            text = span["text"].strip()
                            bbox = span["bbox"]
                            
                            # Calculate position score (center-weighted, top-weighted)
                            x_center = (bbox[0] + bbox[2]) / 2
                            y_pos = bbox[1]
                            center_score = 1 - abs(x_center - page_width/2) / (page_width/2)
                            top_score = 1 - y_pos / page_height
                            position_score = (center_score * 0.7 + top_score * 0.3) # More weight to horizontal center
                            
                            # Only consider text that is large enough and not just numbers/short words
                            if (font_size > page_height * current_config["min_title_font_size_ratio"] and 
                                len(text) > current_config["min_heading_chars"] and 
                                not text.isdigit() and
                                position_score > current_config["min_title_position_score"] and
                                is_likely_heading(text, current_config, font_size, page_dominant_font_sizes.get(page_num, 0), is_bold(span), page_height, is_title_candidate=True)): 
                                
                                title_candidates.append({
                                    "text": text,
                                    "font_size": font_size,
                                    "position_score": position_score,
                                    "page": page_num + 1,
                                    "is_bold": is_bold(span),
                                    "y_pos": y_pos
                                })
        
        # Score and select best title candidate
        if title_candidates:
            # Sort by font size first, then position, then boldness
            title_candidates.sort(key=lambda x: (x["font_size"], x["position_score"], x["is_bold"]), reverse=True)
            
            # Filter out candidates that are too close to each other vertically, keeping the highest scored
            filtered_candidates = []
            for candidate in title_candidates:
                is_duplicate = False
                for existing in filtered_candidates:
                    # If texts are similar and on the same page, and y_pos is close
                    if (candidate["page"] == existing["page"] and 
                       abs(candidate["y_pos"] - existing["y_pos"]) < current_config["line_height_threshold_ratio"] * candidate["font_size"] and 
                       nltk.edit_distance(candidate["text"].lower(), existing["text"].lower()) < max(len(candidate["text"]), len(existing["text"])) * 0.3):
                        is_duplicate = True
                        break
                if not is_duplicate:
                    filtered_candidates.append(candidate)

            if filtered_candidates:
                # Re-score and select the best candidate from the filtered list
                for candidate in filtered_candidates:
                    font_score = candidate["font_size"] / max(c["font_size"] for c in filtered_candidates)
                    bold_score = 1.2 if candidate["is_bold"] else 1.0
                    semantic_score = 1.5 if is_likely_heading(candidate["text"], current_config, candidate["font_size"], page_dominant_font_sizes.get(candidate["page"] - 1, 0), is_bold(span), page_height, is_title_candidate=True) else 1.0
                    
                    candidate["total_score"] = (
                        font_score * current_config["font_weight"] +
                        candidate["position_score"] * current_config["position_weight"] +
                        semantic_score * current_config["semantic_weight"]
                    ) * bold_score
                
                best_candidate = max(filtered_candidates, key=lambda x: x["total_score"])
                title = best_candidate["text"]

    # 2. Enhanced Heading Extraction
    # Collect all text spans with comprehensive analysis
    all_spans_with_pos = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_blocks = page.get_text("dict")["blocks"]
        page_height = page.rect.height
        page_width = page.rect.width
        
        for block in text_blocks:
            if "lines" in block: 
                for line in block["lines"]:
                    for span in line["spans"]:
                        bbox = span["bbox"]
                        x_center = (bbox[0] + bbox[2]) / 2
                        y_pos = bbox[1]
                        
                        # Calculate position-based features
                        is_left_aligned = bbox[0] < page_width * 0.2
                        is_center_aligned = abs(x_center - page_width/2) < page_width * 0.1
                        is_top_of_page = y_pos < page_height * 0.2
                        
                        all_spans_with_pos.append({
                            "text": span["text"].strip(),
                            "size": span["size"],
                            "flags": span["flags"],
                            "page": page_num + 1,
                            "bbox": bbox,
                            "is_left_aligned": is_left_aligned,
                            "is_center_aligned": is_center_aligned,
                            "is_top_of_page": is_top_of_page,
                            "x_center": x_center,
                            "y_pos": y_pos
                        })

    # Enhanced heading detection with multi-factor analysis
    heading_candidates = []
    
    for span in all_spans_with_pos:
        text = span["text"]
        size = span["size"]
        page = span["page"]
        is_bold_text = is_bold(span)
        dominant_size = page_dominant_font_sizes.get(page - 1, 0)

        # Apply ignore patterns
        if any(re.match(pattern, text, re.IGNORECASE) for pattern in current_config["ignore_patterns"]):
            continue

        # Basic filters
        if not text or len(text) < current_config["min_heading_chars"] or text.isdigit():
            continue
        
        if len(text) > current_config["max_heading_chars"]:
            continue

        # Multi-factor scoring for heading detection
        font_score = 0

        # Prioritize larger font sizes relative to dominant text
        if dominant_size > 0:
            if size >= dominant_size * current_config["h1_font_size_multiplier"]:
                font_score = 3
            elif size >= dominant_size * current_config["h2_font_size_multiplier"]:
                font_score = 2
            elif size >= dominant_size * current_config["h3_font_size_multiplier"]:
                font_score = 1
        
        # Fallback to absolute thresholds if dominant size is not useful or too small
        if font_score == 0 and size >= current_config["min_heading_font_size_ratio"] * page_height:
            if size >= h_thresholds["H1"]:
                font_score = 3
            elif size >= h_thresholds["H2"]:
                font_score = 2
            elif size >= h_thresholds["H3"]:
                font_score = 1

        if font_score > 0:
            # Calculate composite score
            bold_bonus = 1.5 if is_bold_text else 1.0
            semantic_bonus = 1.3 if is_likely_heading(text, current_config, size, dominant_size, is_bold_text, page_height) else 1.0
            position_bonus = 1.2 if (span["is_left_aligned"] or span["is_center_aligned"]) else 1.0
            
            total_score = font_score * bold_bonus * semantic_bonus * position_bonus
            
            # Determine heading level based on font score and relative size
            level = "H3" # Default to H3
            if dominant_size > 0:
                if size >= dominant_size * current_config["h1_font_size_multiplier"]:
                    level = "H1"
                elif size >= dominant_size * current_config["h2_font_size_multiplier"]:
                    level = "H2"
                elif size >= dominant_size * current_config["h3_font_size_multiplier"]:
                    level = "H3"
            else: # Fallback to absolute thresholds
                if size >= h_thresholds["H1"]:
                    level = "H1"
                elif size >= h_thresholds["H2"]:
                    level = "H2"
                elif size >= h_thresholds["H3"]:
                    level = "H3"
            
            heading_candidates.append({
                "level": level,
                "text": text,
                "page": page,
                "score": total_score,
                "font_size": size,
                "y_pos": span["y_pos"]
            })

    # Sort by page and then by y_pos to maintain document order
    heading_candidates.sort(key=lambda x: (x["page"], x["y_pos"]))
    
    # Deduplicate and finalize outline, prioritizing higher levels for same text/position
    final_outline = []
    seen_entries = set()

    for candidate in heading_candidates:
        # Create a unique key for deduplication, considering text and approximate position
        # Use a rounded y_pos to group very close lines that might be part of the same heading
        key = (candidate["text"].lower(), candidate["page"], round(candidate["y_pos"] / 10))
        
        if key not in seen_entries:
            # Check if a higher-level heading with similar text already exists on the same page
            is_redundant = False
            for existing_entry in final_outline:
                if (existing_entry["page"] == candidate["page"] and 
                   nltk.edit_distance(existing_entry["text"].lower(), candidate["text"].lower()) < max(len(existing_entry["text"]), len(candidate["text"])) * 0.2 and 
                   (existing_entry["level"] == "H1" and candidate["level"] != "H1" or 
                    existing_entry["level"] == "H2" and candidate["level"] == "H3")):
                    is_redundant = True
                    break
            
            if not is_redundant:
                final_outline.append({
                    "level": candidate["level"],
                    "text": candidate["text"],
                    "page": candidate["page"]
                })
                seen_entries.add(key)

    doc.close()
    return {"title": title, "outline": final_outline}

if __name__ == '__main__':
    # Example usage (for local testing)
    pdf_file = "/app/input/TE_IT_HCIL_Labmanual_Updated.pdf"
    output_file = "/app/output/TE_IT_HCIL_Labmanual_Updated.json"
    
    # Ensure input and output directories exist for local testing
    import os
    os.makedirs(os.path.dirname(pdf_file), exist_ok=True)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    try:
        result = extract_outline(pdf_file)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Outline extracted and saved to {output_file}")
    except Exception as e:
        print(f"Error: {e}")



