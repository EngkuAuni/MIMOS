# Creates PDF report

import os
import tempfile
import datetime
from weasyprint import HTML
from PIL import Image

class PDFGenerator:
    """Generate PDF reports for verification results."""
    
    def __init__(self):
        """Initialize the PDF generator."""
        pass
    
    def generate_report(self, image_path, ocr_text, verification_result, diff_html=None, explanation=None):
        """
        Generate a PDF report for verification results.
        
        Args:
            image_path: Path to the original image
            ocr_text: Text extracted by OCR
            verification_result: Result from TextVerifier
            diff_html: Optional HTML diff
            explanation: Optional LLM explanation
            
        Returns:
            Path to the generated PDF file
        """
        # Prepare HTML content
        html_content = self._build_html_report(
            image_path, ocr_text, verification_result, diff_html, explanation
        )
        
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
            pdf_path = temp.name
        
        # Generate PDF using WeasyPrint
        HTML(string=html_content).write_pdf(pdf_path)
        
        return pdf_path
    
    def _build_html_report(self, image_path, ocr_text, verification_result, diff_html=None, explanation=None):
        """Build HTML content for the report."""
        # Determine verification status badge
        if verification_result['status'] == 'exact':
            badge = '✅ Verified'
            badge_color = '#4CAF50'  # Green
        elif verification_result['status'] == 'near':
            badge = '⚠️ Near Match'
            badge_color = '#FF9800'  # Amber
        else:
            badge = '❌ No Match'
            badge_color = '#F44336'  # Red
        
        # Get ayah information if available
        ayah_info = ""
        if verification_result['ayah']:
            sura, aya = verification_result['ayah']
            ayah_info = f"Surah {sura}, Ayah {aya}"
        
        # Format the date
        date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create image tag (convert to base64 for embedding)
        image_tag = f'<img src="{image_path}" style="max-width: 100%; max-height: 400px;">'
        
        # Build HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Quran Verification Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .badge {{ display: inline-block; padding: 8px 16px; border-radius: 4px; font-weight: bold; color: white; background-color: {badge_color}; }}
                .section {{ margin-bottom: 20px; }}
                .image-container {{ text-align: center; margin-bottom: 20px; }}
                .info-table {{ width: 100%; border-collapse: collapse; }}
                .info-table td, .info-table th {{ border: 1px solid #ddd; padding: 8px; }}
                .info-table tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .rtl {{ direction: rtl; text-align: right; }}
                .diff-container {{ border: 1px solid #ddd; padding: 10px; margin-bottom: 20px; }}
                .explanation {{ padding: 10px; border-left: 4px solid #2196F3; background-color: #E3F2FD; }}
                footer {{ text-align: center; margin-top: 30px; font-size: 0.8em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Quran Verification Report</h1>
                <div class="badge">{badge}</div>
                <p>{date_str}</p>
            </div>
            
            <div class="section">
                <h2>Scanned Image</h2>
                <div class="image-container">
                    {image_tag}
                </div>
            </div>
            
            <div class="section">
                <h2>Verification Results</h2>
                <table class="info-table">
                    <tr>
                        <th>Status</th>
                        <td>{verification_result['status']}</td>
                    </tr>
                    <tr>
                        <th>Ayah</th>
                        <td>{ayah_info}</td>
                    </tr>
                    <tr>
                        <th>Similarity</th>
                        <td>{verification_result['similarity']:.2%}</td>
                    </tr>
                    <tr>
                        <th>Match Type</th>
                        <td>{verification_result['match_type'] or 'N/A'}</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <h2>OCR Text</h2>
                <div class="rtl">
                    <p>{ocr_text}</p>
                </div>
            </div>
        """
        
        # Add reference text if available
        if verification_result['text']:
            html += f"""
            <div class="section">
                <h2>Reference Text</h2>
                <div class="rtl">
                    <p>{verification_result['text']}</p>
                </div>
            </div>
            """
        
        # Add diff if available
        if diff_html:
            html += f"""
            <div class="section">
                <h2>Differences</h2>
                <div class="diff-container">
                    {diff_html}
                </div>
            </div>
            """
        
        # Add explanation if available
        if explanation:
            html += f"""
            <div class="section">
                <h2>Explanation</h2>
                <div class="explanation">
                    <p>{explanation}</p>
                </div>
            </div>
            """
        
        # Add footer
        html += f"""
            <footer>
                <p>Generated by Quran Verificator</p>
            </footer>
        </body>
        </html>
        """
        
        return html