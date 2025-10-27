"""
Malay Report Generator for KDN Compliance
Generates reports in Malay language as required by KDN standards
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from KDN_COMPLIANCE_CONFIG import MALAY_REPORT_TEMPLATES, KDN_ERROR_CATEGORIES

class MalayReportGenerator:
    """Generate KDN-compliant reports in Malay language"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_malay_styles()
        self._register_fonts()
    
    def _setup_malay_styles(self):
        """Setup Malay-specific paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='MalayTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='MalaySubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='MalaySection',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='MalayBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        # Error text style
        self.styles.add(ParagraphStyle(
            name='MalayError',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            fontName='Helvetica',
            textColor=colors.red
        ))
    
    def _register_fonts(self):
        """Register fonts for Malay text support"""
        try:
            # Try to register Malay-compatible fonts
            # You may need to install additional fonts for better Malay support
            pass
        except:
            # Fallback to default fonts
            pass
    
    def generate_kdn_report(self, verification_results: Dict, output_path: str = None) -> str:
        """
        Generate KDN-compliant verification report in Malay
        
        Args:
            verification_results: Results from KDN verification
            output_path: Output file path (optional)
            
        Returns:
            Path to generated report
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/laporan_penyemakan_{timestamp}.pdf"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Add header
        story.extend(self._create_header())
        
        # Add summary section
        story.extend(self._create_summary_section(verification_results))
        
        # Add errors section
        story.extend(self._create_errors_section(verification_results))
        
        # Add recommendations section
        story.extend(self._create_recommendations_section(verification_results))
        
        # Add compliance section
        story.extend(self._create_compliance_section(verification_results))
        
        # Add footer
        story.extend(self._create_footer())
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def _create_header(self) -> List:
        """Create report header"""
        elements = []
        
        # Main title
        elements.append(Paragraph(MALAY_REPORT_TEMPLATES['header'], self.styles['MalayTitle']))
        elements.append(Spacer(1, 12))
        
        # Subtitle
        elements.append(Paragraph(MALAY_REPORT_TEMPLATES['subtitle'], self.styles['MalaySubtitle']))
        elements.append(Spacer(1, 20))
        
        # Report info
        report_info = f"""
        <b>Tarikh Laporan:</b> {datetime.now().strftime("%d %B %Y")}<br/>
        <b>Masa Laporan:</b> {datetime.now().strftime("%H:%M:%S")}<br/>
        <b>Status:</b> Laporan Penyemakan Al-Quran
        """
        elements.append(Paragraph(report_info, self.styles['MalayBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_summary_section(self, results: Dict) -> List:
        """Create summary section"""
        elements = []
        
        # Section header
        elements.append(Paragraph(MALAY_REPORT_TEMPLATES['sections']['summary'], self.styles['MalaySection']))
        
        # Overall compliance status
        compliance = results.get('compliance_status', {})
        overall_compliance = compliance.get('overall_compliance', False)
        
        status_text = "✅ LULUS" if overall_compliance else "❌ TIDAK LULUS"
        status_color = "green" if overall_compliance else "red"
        
        elements.append(Paragraph(f"<b>Status Keseluruhan:</b> <font color='{status_color}'>{status_text}</font>", self.styles['MalayBody']))
        elements.append(Spacer(1, 12))
        
        # Accuracy scores
        accuracy_scores = results.get('accuracy_scores', {})
        
        accuracy_data = [
            ['Aspek', 'Ketepatan', 'Sasaran', 'Status'],
            ['Huruf', f"{accuracy_scores.get('character', 0):.1%}", "99.9%", "✅" if accuracy_scores.get('character', 0) >= 0.999 else "❌"],
            ['Diacritics', f"{accuracy_scores.get('diacritic', 0):.1%}", "99.9%", "✅" if accuracy_scores.get('diacritic', 0) >= 0.999 else "❌"],
            ['Perkataan', f"{accuracy_scores.get('word', 0):.1%}", "99.9%", "✅" if accuracy_scores.get('word', 0) >= 0.999 else "❌"],
            ['Ayat', f"{accuracy_scores.get('verse', 0):.1%}", "99.9%", "✅" if accuracy_scores.get('verse', 0) >= 0.999 else "❌"]
        ]
        
        accuracy_table = Table(accuracy_data)
        accuracy_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(accuracy_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_errors_section(self, results: Dict) -> List:
        """Create errors section"""
        elements = []
        
        # Section header
        elements.append(Paragraph(MALAY_REPORT_TEMPLATES['sections']['errors_found'], self.styles['MalaySection']))
        
        errors = results.get('errors_found', [])
        
        if not errors:
            elements.append(Paragraph("✅ Tiada kesalahan ditemui. Teks mematuhi piawaian KDN.", self.styles['MalayBody']))
            elements.append(Spacer(1, 20))
            return elements
        
        # Error summary
        critical_errors = [e for e in errors if e.category == 'CRITICAL']
        major_errors = [e for e in errors if e.category == 'MAJOR']
        minor_errors = [e for e in errors if e.category == 'MINOR']
        
        error_summary = f"""
        <b>Ringkasan Kesalahan:</b><br/>
        • Kesalahan Kritikal: {len(critical_errors)}<br/>
        • Kesalahan Utama: {len(major_errors)}<br/>
        • Kesalahan Kecil: {len(minor_errors)}<br/>
        • Jumlah Kesalahan: {len(errors)}
        """
        elements.append(Paragraph(error_summary, self.styles['MalayBody']))
        elements.append(Spacer(1, 12))
        
        # Detailed errors
        for i, error in enumerate(errors, 1):
            error_text = f"""
            <b>{i}. {error.type.upper()}</b><br/>
            <b>Kategori:</b> {KDN_ERROR_CATEGORIES.get(error.category, {}).get('name', error.category)}<br/>
            <b>Penerangan:</b> {error.description}<br/>
            <b>Kedudukan:</b> {error.position}<br/>
            <b>Teks Ditemui:</b> {error.extracted_text}<br/>
            <b>Teks Betul:</b> {error.correct_text}<br/>
            <b>Cadangan:</b> {error.suggestion}<br/>
            <b>Rujukan KDN:</b> {error.kdn_reference}
            """
            elements.append(Paragraph(error_text, self.styles['MalayError']))
            elements.append(Spacer(1, 8))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _create_recommendations_section(self, results: Dict) -> List:
        """Create recommendations section"""
        elements = []
        
        # Section header
        elements.append(Paragraph(MALAY_REPORT_TEMPLATES['sections']['recommendations'], self.styles['MalaySection']))
        
        recommendations = results.get('recommendations', [])
        
        if not recommendations:
            elements.append(Paragraph("✅ Tiada cadangan khas. Teks mematuhi semua piawaian.", self.styles['MalayBody']))
            elements.append(Spacer(1, 20))
            return elements
        
        # List recommendations
        for i, recommendation in enumerate(recommendations, 1):
            elements.append(Paragraph(f"{i}. {recommendation}", self.styles['MalayBody']))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _create_compliance_section(self, results: Dict) -> List:
        """Create compliance section"""
        elements = []
        
        # Section header
        elements.append(Paragraph(MALAY_REPORT_TEMPLATES['sections']['compliance'], self.styles['MalaySection']))
        
        compliance = results.get('compliance_status', {})
        kdn_standards_met = results.get('kdn_standards_met', False)
        
        # Compliance status
        compliance_text = f"""
        <b>Status Pematuhan Piawaian KDN:</b><br/>
        • Pematuhan Huruf: {'✅' if compliance.get('character_compliance', False) else '❌'}<br/>
        • Pematuhan Diacritics: {'✅' if compliance.get('diacritic_compliance', False) else '❌'}<br/>
        • Pematuhan Perkataan: {'✅' if compliance.get('word_compliance', False) else '❌'}<br/>
        • Pematuhan Ayat: {'✅' if compliance.get('verse_compliance', False) else '❌'}<br/>
        • Piawaian KDN: {'✅ DIPATUHI' if kdn_standards_met else '❌ TIDAK DIPATUHI'}
        """
        elements.append(Paragraph(compliance_text, self.styles['MalayBody']))
        elements.append(Spacer(1, 12))
        
        # KDN standards reference
        standards_text = """
        <b>Rujukan Piawaian KDN:</b><br/>
        • Garis Panduan Kaedah Penyemakan Al-Quran<br/>
        • SENARAI KESALAHAN BIASA BERLAKU<br/>
        • Piawaian Mushaf Uthmani Malaysia
        """
        elements.append(Paragraph(standards_text, self.styles['MalayBody']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_footer(self) -> List:
        """Create report footer"""
        elements = []
        
        # Footer line
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("─" * 50, self.styles['MalayBody']))
        
        # Footer text
        footer_text = f"""
        <b>Sistem Verifikasi Al-Quran - KDN</b><br/>
        Laporan dijana pada: {datetime.now().strftime("%d %B %Y, %H:%M:%S")}<br/>
        Versi Sistem: 1.0 | Piawaian: KDN Compliant
        """
        elements.append(Paragraph(footer_text, self.styles['MalayBody']))
        
        return elements
    
    def generate_html_report(self, verification_results: Dict, output_path: str = None) -> str:
        """Generate HTML version of the report"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/laporan_penyemakan_{timestamp}.html"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate HTML content
        html_content = self._generate_html_content(verification_results)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_html_content(self, results: Dict) -> str:
        """Generate HTML content for the report"""
        compliance = results.get('compliance_status', {})
        accuracy_scores = results.get('accuracy_scores', {})
        errors = results.get('errors_found', [])
        recommendations = results.get('recommendations', [])
        
        html = f"""
        <!DOCTYPE html>
        <html lang="ms">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Laporan Penyemakan Al-Quran - KDN</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .title {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .subtitle {{ font-size: 16px; color: #7f8c8d; margin-top: 10px; }}
                .section {{ margin: 20px 0; }}
                .section-title {{ font-size: 18px; font-weight: bold; color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
                .error {{ background-color: #fdf2f2; border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; }}
                .success {{ background-color: #f0f9ff; border-left: 4px solid #27ae60; padding: 10px; margin: 10px 0; }}
                .table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .table th {{ background-color: #f2f2f2; font-weight: bold; }}
                .status-pass {{ color: #27ae60; font-weight: bold; }}
                .status-fail {{ color: #e74c3c; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">{MALAY_REPORT_TEMPLATES['header']}</div>
                <div class="subtitle">{MALAY_REPORT_TEMPLATES['subtitle']}</div>
                <p>Tarikh: {datetime.now().strftime("%d %B %Y")} | Masa: {datetime.now().strftime("%H:%M:%S")}</p>
            </div>
            
            <div class="section">
                <div class="section-title">{MALAY_REPORT_TEMPLATES['sections']['summary']}</div>
                <div class="{'success' if compliance.get('overall_compliance', False) else 'error'}">
                    <strong>Status Keseluruhan:</strong> {'LULUS' if compliance.get('overall_compliance', False) else 'TIDAK LULUS'}
                </div>
                
                <table class="table">
                    <tr><th>Aspek</th><th>Ketepatan</th><th>Sasaran</th><th>Status</th></tr>
                    <tr><td>Huruf</td><td>{accuracy_scores.get('character', 0):.1%}</td><td>99.9%</td><td class="{'status-pass' if accuracy_scores.get('character', 0) >= 0.999 else 'status-fail'}">{'✅' if accuracy_scores.get('character', 0) >= 0.999 else '❌'}</td></tr>
                    <tr><td>Diacritics</td><td>{accuracy_scores.get('diacritic', 0):.1%}</td><td>99.9%</td><td class="{'status-pass' if accuracy_scores.get('diacritic', 0) >= 0.999 else 'status-fail'}">{'✅' if accuracy_scores.get('diacritic', 0) >= 0.999 else '❌'}</td></tr>
                    <tr><td>Perkataan</td><td>{accuracy_scores.get('word', 0):.1%}</td><td>99.9%</td><td class="{'status-pass' if accuracy_scores.get('word', 0) >= 0.999 else 'status-fail'}">{'✅' if accuracy_scores.get('word', 0) >= 0.999 else '❌'}</td></tr>
                    <tr><td>Ayat</td><td>{accuracy_scores.get('verse', 0):.1%}</td><td>99.9%</td><td class="{'status-pass' if accuracy_scores.get('verse', 0) >= 0.999 else 'status-fail'}">{'✅' if accuracy_scores.get('verse', 0) >= 0.999 else '❌'}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <div class="section-title">{MALAY_REPORT_TEMPLATES['sections']['errors_found']}</div>
                {self._generate_errors_html(errors)}
            </div>
            
            <div class="section">
                <div class="section-title">{MALAY_REPORT_TEMPLATES['sections']['recommendations']}</div>
                {self._generate_recommendations_html(recommendations)}
            </div>
            
            <div class="section">
                <div class="section-title">{MALAY_REPORT_TEMPLATES['sections']['compliance']}</div>
                <p><strong>Piawaian KDN:</strong> {'✅ DIPATUHI' if results.get('kdn_standards_met', False) else '❌ TIDAK DIPATUHI'}</p>
            </div>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #7f8c8d;">
                <p>Sistem Verifikasi Al-Quran - KDN | Dijana pada: {datetime.now().strftime("%d %B %Y, %H:%M:%S")}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_errors_html(self, errors: List) -> str:
        """Generate HTML for errors section"""
        if not errors:
            return '<div class="success">✅ Tiada kesalahan ditemui. Teks mematuhi piawaian KDN.</div>'
        
        html = ""
        for i, error in enumerate(errors, 1):
            html += f"""
            <div class="error">
                <strong>{i}. {error.type.upper()}</strong><br/>
                <strong>Kategori:</strong> {KDN_ERROR_CATEGORIES.get(error.category, {}).get('name', error.category)}<br/>
                <strong>Penerangan:</strong> {error.description}<br/>
                <strong>Kedudukan:</strong> {error.position}<br/>
                <strong>Teks Ditemui:</strong> {error.extracted_text}<br/>
                <strong>Teks Betul:</strong> {error.correct_text}<br/>
                <strong>Cadangan:</strong> {error.suggestion}
            </div>
            """
        
        return html
    
    def _generate_recommendations_html(self, recommendations: List) -> str:
        """Generate HTML for recommendations section"""
        if not recommendations:
            return '<div class="success">✅ Tiada cadangan khas. Teks mematuhi semua piawaian.</div>'
        
        html = "<ol>"
        for recommendation in recommendations:
            html += f"<li>{recommendation}</li>"
        html += "</ol>"
        
        return html
