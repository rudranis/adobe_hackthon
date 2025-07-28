# Configuration for PDF Outline Extraction

# Font size thresholds for heading detection
HEADING_FONT_SIZE_THRESHOLDS = {
    "H1": 18,
    "H2": 14,
    "H3": 12,
}

# Keyword-based scoring for semantic analysis
HEADING_KEYWORDS = {
    "H1": ["chapter", "part", "section"],
    "H2": ["introduction", "conclusion", "summary", "references"],
    "H3": ["theory", "methodology", "results", "discussion"],
}

DEFAULT_CONFIG = {
    "min_title_font_size_ratio": 0.02,  # Minimum font size for title relative to page height
    "min_heading_font_size_ratio": 0.015, # Minimum font size for headings relative to page height
    "h1_font_size_multiplier": 1.5, # H1 font size relative to dominant font size
    "h2_font_size_multiplier": 1.2, # H2 font size relative to dominant font size
    "h3_font_size_multiplier": 1.0, # H3 font size relative to dominant font size
    "bold_weight_factor": 1.2, # Factor to boost bold text importance
    "line_height_threshold_ratio": 0.8, # For grouping lines into blocks
    "max_heading_chars": 120, # Max characters for a heading
    "min_heading_chars": 3, # Min characters for a heading
    "position_weight": 0.1, # Weight for position-based scoring
    "semantic_weight": 0.3, # Weight for semantic analysis
    "font_weight": 0.6, # Weight for font-based analysis
    "title_search_pages": 5, # Number of initial pages to search for the title
    "min_title_position_score": 0.7, # Minimum position score for a title candidate
    "ignore_patterns": [
        r"^\\d+\\.$", # Just numbers with dots
        r"^Fig\\.\\s*\\d+", # Figure captions
        r"^Table\\s*\\d+", # Table captions
        r"^\\s*$", # Empty lines
        r"^Page\\s*\\d+", # Page numbers
        r"^\\d+\\s*$", # Just numbers
        r"SCTR\\\s*\\\"s", # Specific header text
        r"PUNE INSTITUTE OF COMPUTER TECHNOLOGY", # Specific header text
        r"DEPARTMENT OF INFORMATION TECHNOLOGY", # Specific footer text
    ]
}



