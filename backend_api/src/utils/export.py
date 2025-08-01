import os
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.colors import darkblue
import logging

from .database import db

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting journal entries"""
    
    def __init__(self):
        self.export_dir = os.path.join("data", "exports")
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_to_txt(self, user_id: str, entries: List[Dict[str, Any]], 
                      filename: str = None) -> str:
        """Export entries to TXT file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"journal_export_{timestamp}.txt"
        
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write("JOURNAL ENTRIES EXPORT\n")
                f.write("=" * 50 + "\n")
                f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Entries: {len(entries)}\n")
                f.write("=" * 50 + "\n\n")
                
                # Write entries
                for i, entry in enumerate(entries, 1):
                    f.write(f"Entry #{i}\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"Title: {entry.get('title', 'Untitled')}\n")
                    f.write(f"Date: {self._format_date(entry.get('created_at'))}\n")
                    
                    if entry.get('mood'):
                        f.write(f"Mood: {entry.get('mood').replace('_', ' ').title()}\n")
                    
                    if entry.get('tags'):
                        f.write(f"Tags: {', '.join(entry.get('tags', []))}\n")
                    
                    f.write("\nContent:\n")
                    f.write(entry.get('content', '') + "\n")
                    f.write("\n" + "=" * 50 + "\n\n")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting to TXT: {e}")
            raise Exception(f"Failed to export to TXT: {str(e)}")
    
    def export_to_pdf(self, user_id: str, entries: List[Dict[str, Any]], 
                      filename: str = None) -> str:
        """Export entries to PDF file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"journal_export_{timestamp}.pdf"
        
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Get user info
            user = db.get_user_by_id(user_id)
            user_name = user.get('full_name') or user.get('username', 'Unknown')
            
            # Build PDF content
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=darkblue,
                alignment=1  # Center alignment
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=darkblue
            )
            
            # Title page
            story.append(Paragraph("Journal Entries Export", title_style))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"User: {user_name}", styles['Normal']))
            story.append(Paragraph(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Paragraph(f"Total Entries: {len(entries)}", styles['Normal']))
            story.append(Spacer(1, 30))
            
            # Entries
            for i, entry in enumerate(entries, 1):
                # Entry header
                story.append(Paragraph(f"Entry #{i}: {entry.get('title', 'Untitled')}", heading_style))
                
                # Entry metadata
                metadata = []
                metadata.append(f"Date: {self._format_date(entry.get('created_at'))}")
                
                if entry.get('mood'):
                    metadata.append(f"Mood: {entry.get('mood').replace('_', ' ').title()}")
                
                if entry.get('tags'):
                    metadata.append(f"Tags: {', '.join(entry.get('tags', []))}")
                
                for meta in metadata:
                    story.append(Paragraph(meta, styles['Normal']))
                
                story.append(Spacer(1, 12))
                
                # Entry content
                content = entry.get('content', '').replace('\n', '<br/>')
                story.append(Paragraph(content, styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(story)
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            raise Exception(f"Failed to export to PDF: {str(e)}")
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        try:
            if isinstance(date_str, str):
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return str(date_str)
        except:
            return str(date_str)
    
    def cleanup_old_exports(self, days_old: int = 7):
        """Clean up old export files"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            for filename in os.listdir(self.export_dir):
                filepath = os.path.join(self.export_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old export file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up exports: {e}")


# Global export service instance
export_service = ExportService()
