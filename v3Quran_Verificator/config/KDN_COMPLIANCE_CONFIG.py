"""
KDN Compliance Configuration
Based on "Garis Panduan Kaedah Penyemakan Al-Quran" and "SENARAI KESALAHAN BIASA BERLAKU"
"""

# Error Categories from KDN Guidelines
# Based on "Garis Panduan Kaedah Penyemakan Al-Quran" and "SENARAI KESALAHAN BIASA BERLAKU"
KDN_ERROR_CATEGORIES = {
    "CRITICAL": {
        "name": "Kesalahan Kritikal",
        "description": "Kesalahan yang mengubah makna ayat dan mempengaruhi pemahaman",
        "examples": [
            "Penggantian huruf yang mengubah makna (contoh: ب menjadi ت)",
            "Penambahan atau pengurangan kata dalam ayat",
            "Kesalahan dalam struktur ayat yang mengubah konteks",
            "Penggantian kata ganti (contoh: هو menjadi هي)",
            "Kesalahan dalam tanda baca yang mengubah makna"
        ],
        "severity": "high",
        "threshold": 0.999,  # 99.9%+ accuracy required
        "kdn_reference": "Garis Panduan - Bahagian 3.1"
    },
    "MAJOR": {
        "name": "Kesalahan Utama", 
        "description": "Kesalahan yang mempengaruhi bacaan tetapi tidak mengubah makna asas",
        "examples": [
            "Kesalahan diacritics (harakat, shaddah, sukun) yang mempengaruhi tajwid",
            "Kesalahan dalam bentuk huruf yang tidak mengubah makna",
            "Kesalahan dalam spacing yang mempengaruhi bacaan",
            "Kesalahan dalam hamza (ء) dan alif (ا)",
            "Kesalahan dalam tanween (ً ٌ ٍ)"
        ],
        "severity": "high",
        "threshold": 0.998,  # 99.8%+ accuracy required
        "kdn_reference": "SENARAI KESALAHAN - Kategori A"
    },
    "MINOR": {
        "name": "Kesalahan Kecil",
        "description": "Kesalahan yang tidak mempengaruhi makna atau bacaan secara signifikan",
        "examples": [
            "Kesalahan dalam font styling atau ketebalan huruf",
            "Kesalahan dalam margin atau spacing yang tidak mempengaruhi bacaan",
            "Kesalahan dalam layout yang tidak mengganggu pemahaman",
            "Kesalahan dalam penomboran halaman",
            "Kesalahan dalam format tajuk surah"
        ],
        "severity": "medium", 
        "threshold": 0.995,  # 99.5%+ accuracy required
        "kdn_reference": "SENARAI KESALAHAN - Kategori B"
    }
}

# Specific Error Types from KDN Guidelines
KDN_ERROR_TYPES = {
    "diacritic_errors": {
        "fatha_missing": "Fatha hilang",
        "damma_missing": "Damma hilang", 
        "kasra_missing": "Kasra hilang",
        "shadda_missing": "Shadda hilang",
        "sukun_missing": "Sukun hilang",
        "tanween_errors": "Kesalahan tanween",
        "hamza_errors": "Kesalahan hamza"
    },
    "character_errors": {
        "letter_substitution": "Penggantian huruf",
        "letter_addition": "Penambahan huruf",
        "letter_deletion": "Penghapusan huruf",
        "letter_inversion": "Pembalikan huruf",
        "similar_letter_confusion": "Kekeliruan huruf serupa"
    },
    "layout_errors": {
        "spacing_errors": "Kesalahan jarak",
        "line_break_errors": "Kesalahan pemisahan baris",
        "margin_errors": "Kesalahan margin",
        "alignment_errors": "Kesalahan penjajaran"
    },
    "structural_errors": {
        "verse_separation": "Kesalahan pemisahan ayat",
        "surah_title": "Kesalahan tajuk surah",
        "bismillah_errors": "Kesalahan bismillah",
        "page_numbering": "Kesalahan penomboran halaman"
    }
}

# Performance Requirements
PERFORMANCE_CONFIG = {
    "target_pages_per_hour": 100,
    "max_processing_time_per_page": 36,  # seconds (100 pages/hour)
    "concurrent_processing": True,
    "batch_size": 4,  # Process 4 pages simultaneously
    "memory_limit_gb": 8,
    "gpu_acceleration": True
}

# Accuracy Requirements (as close to 100% as possible)
ACCURACY_CONFIG = {
    "character_accuracy": {
        "target": 0.999,  # 99.9%
        "minimum": 0.995,  # 99.5%
        "critical_threshold": 0.99  # 99%
    },
    "diacritic_accuracy": {
        "target": 0.999,  # 99.9%
        "minimum": 0.995,  # 99.5%
        "critical_threshold": 0.98  # 98%
    },
    "word_accuracy": {
        "target": 0.999,  # 99.9%
        "minimum": 0.995,  # 99.5%
        "critical_threshold": 0.99  # 99%
    },
    "verse_accuracy": {
        "target": 0.999,  # 99.9%
        "minimum": 0.995,  # 99.5%
        "critical_threshold": 0.99  # 99%
    }
}

# Language Support
LANGUAGE_CONFIG = {
    "primary_language": "ar",  # Arabic
    "report_language": "ms",   # Malay
    "ui_language": "en",       # English (for development)
    "supported_languages": ["ar", "ms", "en"]
}

# Report Templates in Malay
MALAY_REPORT_TEMPLATES = {
    "header": "LAPORAN PENYEMAKAN AL-QURAN",
    "subtitle": "Sistem Verifikasi Mushaf Uthmani - KDN",
    "sections": {
        "summary": "RINGKASAN PENYEMAKAN",
        "errors_found": "KESALAHAN YANG DITEMUI",
        "recommendations": "CADANGAN PEMBETULAN",
        "compliance": "PENYELARASAN PIAWAIAN KDN"
    },
    "error_descriptions": {
        "critical": "Kesalahan Kritikal - Perlu pembetulan segera",
        "major": "Kesalahan Utama - Perlu pembetulan",
        "minor": "Kesalahan Kecil - Boleh dibetulkan"
    }
}

# KDN Compliance Standards
KDN_COMPLIANCE_STANDARDS = {
    "mushaf_standards": {
        "font": "Uthmani script only",
        "layout": "Medina Mushaf layout",
        "spacing": "Standard Uthmani spacing",
        "margins": "KDN approved margins"
    },
    "verification_standards": {
        "character_verification": "100% character accuracy required",
        "diacritic_verification": "100% diacritic accuracy required", 
        "layout_verification": "100% layout compliance required",
        "structural_verification": "100% structural accuracy required"
    },
    "reporting_standards": {
        "language": "Malay",
        "format": "PDF with detailed analysis",
        "sections": ["Summary", "Errors", "Recommendations", "Compliance"],
        "approval": "KDN approved format"
    }
}
