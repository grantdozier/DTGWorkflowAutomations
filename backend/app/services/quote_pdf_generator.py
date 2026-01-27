"""
Quote PDF Generator

Generates professional quote PDFs formatted like STINE's Quote 684107
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Optional
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

logger = logging.getLogger(__name__)


class QuotePDFGenerator:
    """
    Generate professional quote PDFs

    Format matches STINE's Quote 684107 style:
    - Company header
    - Quote details (number, date, customer)
    - Line items organized by category
    - Subtotals per category
    - Final totals with overhead, profit, tax
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or "uploads/quotes"
        os.makedirs(self.output_dir, exist_ok=True)

        # Page setup
        self.page_width = letter[0]
        self.page_height = letter[1]
        self.margin = 0.5 * inch

        # Styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Company name style
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=6,
            alignment=TA_LEFT
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
            spaceBefore=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))

        # Quote number style
        self.styles.add(ParagraphStyle(
            name='QuoteNumber',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=TA_RIGHT
        ))

    def generate_quote(
        self,
        quote_data: Dict,
        estimate_data: Dict,
        line_items: List[Dict],
        company_info: Dict,
        project_info: Dict,
        output_filename: str = None
    ) -> str:
        """
        Generate quote PDF

        Args:
            quote_data: Quote metadata (number, date, etc.)
            estimate_data: Estimate breakdown (costs, totals)
            line_items: List of line items with materials
            company_info: Company information
            project_info: Project/customer information
            output_filename: Optional custom filename

        Returns:
            Path to generated PDF file
        """
        if not output_filename:
            quote_num = quote_data.get('quote_number', 'QUOTE')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{quote_num}_{timestamp}.pdf"

        output_path = os.path.join(self.output_dir, output_filename)

        # Create PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )

        # Build content
        story = []

        # Header
        story.extend(self._create_header(company_info, quote_data))
        story.append(Spacer(1, 0.2 * inch))

        # Customer info
        story.extend(self._create_customer_info(project_info, quote_data))
        story.append(Spacer(1, 0.3 * inch))

        # Line items by category
        story.extend(self._create_line_items_table(line_items))
        story.append(Spacer(1, 0.3 * inch))

        # Totals
        story.extend(self._create_totals_table(estimate_data))
        story.append(Spacer(1, 0.3 * inch))

        # Footer
        story.extend(self._create_footer(quote_data))

        # Build PDF
        doc.build(story)

        logger.info(f"Generated quote PDF: {output_path}")
        return output_path

    def _create_header(self, company_info: Dict, quote_data: Dict) -> List:
        """Create company header section - professional layout"""
        elements = []

        # Company name - large and prominent
        company_name = company_info.get('name', 'Company Name')
        name_para = Paragraph(
            f'<font size="24"><b>{company_name}</b></font>',
            self.styles['Normal']
        )
        elements.append(name_para)
        elements.append(Spacer(1, 0.1 * inch))

        # Two-column layout: Company details left, Quote info right
        company_details = f"""
        {company_info.get('address', '')}<br/>
        {company_info.get('city', '')}, {company_info.get('state', '')} {company_info.get('zip', '')}<br/>
        Phone: {company_info.get('phone', '')}
        """
        company_text = Paragraph(company_details, self.styles['Normal'])

        quote_header = f"""
        <font size="20"><b>Quotation</b></font><br/><br/>
        <b>Quote No:</b> {quote_data.get('quote_number', 'N/A')}<br/>
        <b>Quote Date:</b> {quote_data.get('quote_date', datetime.now().strftime('%m/%d/%Y'))}<br/>
        <b>Expiration:</b> {quote_data.get('expiration_date', (datetime.now() + timedelta(days=7)).strftime('%m/%d/%Y'))}
        """
        quote_text = Paragraph(quote_header, self.styles['Normal'])

        header_table = Table(
            [[company_text, quote_text]],
            colWidths=[4.5 * inch, 2.5 * inch]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(header_table)

        # Horizontal line
        elements.append(Spacer(1, 0.1 * inch))
        line_table = Table([['']], colWidths=[7 * inch])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor('#1a1a1a')),
        ]))
        elements.append(line_table)

        return elements

    def _create_customer_info(self, project_info: Dict, quote_data: Dict) -> List:
        """Create customer information section"""
        elements = []

        customer_data = [
            ['Customer:', project_info.get('customer_name', 'N/A')],
            ['Contact:', project_info.get('contact_name', '')],
            ['Job:', project_info.get('name', '')],
            ['Location:', project_info.get('location', '')],
            ['Delivery:', quote_data.get('delivery_date', 'TBD')],
        ]

        customer_table = Table(customer_data, colWidths=[1.5 * inch, 5.5 * inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(customer_table)

        return elements

    def _create_line_items_table(self, line_items: List[Dict]) -> List:
        """Create line items table organized by category - Stine quote style"""
        elements = []

        # Group items by category
        items_by_category = {}
        for item in line_items:
            category = item.get('category', 'Miscellaneous')
            if category not in items_by_category:
                items_by_category[category] = []
            items_by_category[category].append(item)

        # Column widths - wider to prevent wrapping
        col_widths = [0.7 * inch, 0.9 * inch, 3.4 * inch, 0.7 * inch, 0.4 * inch, 0.9 * inch]

        # Table header row
        header_table = Table(
            [['Qty', 'Product Code', 'Description', 'Price', 'Unit', 'Total']],
            colWidths=col_widths
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
            ('ALIGN', (5, 0), (5, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(header_table)

        # Process each category as a separate table for better control
        for category in sorted(items_by_category.keys()):
            # Category header
            cat_header = Table(
                [[Paragraph(f'<b>{category}</b>', self.styles['SectionHeader'])]],
                colWidths=[sum(col_widths)]
            )
            cat_header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F5F5')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(cat_header)

            # Build data rows for this category
            table_data = []
            category_total = Decimal('0')

            for item in items_by_category[category]:
                qty = item.get('quantity', 0)
                code = item.get('product_code', '')
                desc = item.get('description', item.get('label', ''))
                unit_price = item.get('unit_price', 0)
                unit = item.get('unit', 'ea')
                line_total = item.get('line_total', 0)

                category_total += Decimal(str(line_total))

                qty_str = str(int(qty)) if float(qty).is_integer() else str(qty)
                row = [
                    qty_str,
                    code,
                    desc,
                    f'${unit_price:,.2f}',
                    unit,
                    f'${line_total:,.2f}'
                ]
                table_data.append(row)

            # Create items table
            if table_data:
                items_table = Table(table_data, colWidths=col_widths)
                items_table.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),   # Qty right
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # Price right
                    ('ALIGN', (5, 0), (5, -1), 'RIGHT'),   # Total right
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
                ]))
                elements.append(items_table)

            # Category subtotal row
            subtotal_table = Table(
                [[f'End of {category}', f'${category_total:,.2f}']],
                colWidths=[sum(col_widths) - 1.0 * inch, 1.0 * inch]
            )
            subtotal_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEABOVE', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(subtotal_table)
            elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _create_totals_table(self, estimate_data: Dict) -> List:
        """Create totals summary table"""
        elements = []

        # Get values
        materials = estimate_data.get('materials_cost', 0)
        labor = estimate_data.get('labor_cost', 0)
        equipment = estimate_data.get('equipment_cost', 0)
        subcontractor = estimate_data.get('subcontractor_cost', 0)
        subtotal = estimate_data.get('subtotal', 0)
        overhead = estimate_data.get('overhead', 0)
        overhead_pct = estimate_data.get('overhead_percentage', 0)
        profit = estimate_data.get('profit', 0)
        profit_pct = estimate_data.get('profit_percentage', 0)
        total = estimate_data.get('total_cost', 0)
        tax_rate = estimate_data.get('tax_rate', 0)
        tax_amount = estimate_data.get('tax_amount', 0)
        grand_total = estimate_data.get('grand_total', 0)

        # Build totals table
        totals_data = []

        if labor > 0:
            totals_data.append(['Labor Cost:', f'${labor:,.2f}'])
        if equipment > 0:
            totals_data.append(['Equipment Cost:', f'${equipment:,.2f}'])
        if subcontractor > 0:
            totals_data.append(['Subcontractor Cost:', f'${subcontractor:,.2f}'])

        totals_data.extend([
            ['Materials Cost:', f'${materials:,.2f}'],
            ['', ''],
            [Paragraph('<b>Subtotal:</b>', self.styles['Normal']), Paragraph(f'<b>${subtotal:,.2f}</b>', self.styles['Normal'])],
            [f'Overhead ({overhead_pct:.1f}%):', f'${overhead:,.2f}'],
            [f'Profit ({profit_pct:.1f}%):', f'${profit:,.2f}'],
            ['', ''],
            [Paragraph('<b>Total Amount:</b>', self.styles['Normal']), Paragraph(f'<b>${total:,.2f}</b>', self.styles['Normal'])],
            [f'Sales Tax {tax_rate:.1f}%:', f'${tax_amount:,.2f}'],
            ['', ''],
            [Paragraph('<b><font size=11>Quotation Total:</font></b>', self.styles['Normal']),
             Paragraph(f'<b><font size=11>${grand_total:,.2f}</font></b>', self.styles['Normal'])],
        ])

        # Create table (right-aligned)
        totals_table = Table(totals_data, colWidths=[4.5 * inch, 2.5 * inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(totals_table)

        return elements

    def _create_footer(self, quote_data: Dict) -> List:
        """Create footer with terms and signature"""
        elements = []

        elements.append(Spacer(1, 0.2 * inch))

        # Terms
        terms = """
        <b>Terms and Conditions:</b><br/>
        Due to market conditions, prices are subject to change without notification.
        Estimates are subject to errors and omissions. This is only an estimate and not a
        firm bid of materials for your project. It is the customer's / contractor's
        responsibility to verify all quantities and lengths. We only provide material quotes,
        any code or engineering requirements are the customer's responsibility.
        """
        terms_para = Paragraph(terms, self.styles['Normal'])
        elements.append(terms_para)

        elements.append(Spacer(1, 0.3 * inch))

        # Signature line
        sig_text = """
        By your signature below, you are agreeing to the Terms and Conditions set forth above.<br/>
        <br/>
        ___________________________________ &nbsp;&nbsp;&nbsp;&nbsp; _______________<br/>
        Buyer &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Date
        """
        sig_para = Paragraph(sig_text, self.styles['Normal'])
        elements.append(sig_para)

        return elements


def generate_quote_pdf(
    estimate_id: str,
    company_info: Dict,
    project_info: Dict,
    estimate_data: Dict,
    line_items: List[Dict],
    output_dir: str = None
) -> str:
    """
    Convenience function to generate quote PDF

    Args:
        estimate_id: Estimate ID
        company_info: Company information
        project_info: Project/customer information
        estimate_data: Estimate breakdown
        line_items: List of line items
        output_dir: Optional output directory

    Returns:
        Path to generated PDF
    """
    generator = QuotePDFGenerator(output_dir)

    # Generate quote number from estimate ID
    quote_number = f"Q{estimate_id[:8].upper()}"

    quote_data = {
        'quote_number': quote_number,
        'quote_date': datetime.now().strftime('%m/%d/%Y'),
        'expiration_date': (datetime.now() + timedelta(days=7)).strftime('%m/%d/%Y'),
        'delivery_date': 'TBD',
    }

    return generator.generate_quote(
        quote_data=quote_data,
        estimate_data=estimate_data,
        line_items=line_items,
        company_info=company_info,
        project_info=project_info
    )
