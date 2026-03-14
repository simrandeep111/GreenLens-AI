from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


def money(value: Decimal) -> str:
    return f"${value:,.2f}"


def dec(value: str) -> Decimal:
    return Decimal(value)


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class PdfCanvas:
    def __init__(self, width: int = 612, height: int = 792) -> None:
        self.width = width
        self.height = height
        self.commands: list[str] = []

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        stroke: tuple[float, float, float] | None = None,
        fill: tuple[float, float, float] | None = None,
        line_width: float = 1,
    ) -> None:
        parts: list[str] = [f"{line_width:.2f} w"]
        if fill is not None:
            parts.append(f"{fill[0]:.3f} {fill[1]:.3f} {fill[2]:.3f} rg")
        if stroke is not None:
            parts.append(f"{stroke[0]:.3f} {stroke[1]:.3f} {stroke[2]:.3f} RG")
        operator = "B" if fill is not None and stroke is not None else "f" if fill is not None else "S"
        parts.append(f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re {operator}")
        self.commands.append(" ".join(parts))

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        color: tuple[float, float, float] = (0.82, 0.84, 0.87),
        width: float = 1,
    ) -> None:
        self.commands.append(
            f"{width:.2f} w {color[0]:.3f} {color[1]:.3f} {color[2]:.3f} RG {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S"
        )

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        size: int = 12,
        font: str = "F1",
        color: tuple[float, float, float] = (0.16, 0.19, 0.23),
    ) -> None:
        self.commands.append(
            " ".join(
                [
                    "BT",
                    f"/{font} {size} Tf",
                    f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg",
                    f"1 0 0 1 {x:.2f} {y:.2f} Tm",
                    f"({escape_pdf_text(value)}) Tj",
                    "ET",
                ]
            )
        )

    def wrapped_text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        max_chars: int,
        size: int = 11,
        font: str = "F1",
        color: tuple[float, float, float] = (0.27, 0.31, 0.36),
        line_gap: int = 14,
    ) -> float:
        current_y = y
        for line in wrap_text(value, max_chars):
            self.text(x, current_y, line, size=size, font=font, color=color)
            current_y -= line_gap
        return current_y

    def render(self) -> bytes:
        content = "\n".join(self.commands).encode("latin-1", "replace")

        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R >> >> >>",
            f"<< /Length {len(content)} >>\nstream\n".encode("latin-1") + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
        ]

        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1")
        )
        return bytes(pdf)


@dataclass(frozen=True)
class UtilityStatement:
    relative_path: str
    brand: str
    subtitle: str
    accent: tuple[float, float, float]
    title: str
    company_name: str
    company_address: list[str]
    service_address: str
    statement_date: str
    billing_period: str
    account_number: str
    due_date: str
    summary_cards: list[tuple[str, str, str]]
    charges: list[tuple[str, Decimal]]
    footer_note: str


@dataclass(frozen=True)
class VendorInvoice:
    relative_path: str
    brand: str
    subtitle: str
    accent: tuple[float, float, float]
    title: str
    company_name: str
    company_address: list[str]
    vendor_address: list[str]
    invoice_number: str
    invoice_date: str
    due_date: str
    terms: str
    line_items: list[tuple[str, int, Decimal]]
    tax_label: str
    tax_amount: Decimal
    notes: str


@dataclass(frozen=True)
class FuelReceipt:
    relative_path: str
    brand: str
    subtitle: str
    accent: tuple[float, float, float]
    company_name: str
    location: str
    transaction_date: str
    transaction_time: str
    merchant_id: str
    card_reference: str
    odometer: str
    line_items: list[tuple[str, Decimal]]
    total: Decimal
    notes: list[str]


def draw_header(canvas: PdfCanvas, brand: str, subtitle: str, accent: tuple[float, float, float], title: str) -> None:
    canvas.rect(36, 724, 540, 42, fill=accent)
    canvas.text(52, 741, brand, size=20, font="F2", color=(1, 1, 1))
    canvas.text(52, 728, subtitle, size=9, font="F1", color=(0.91, 0.96, 1))
    canvas.text(392, 741, title, size=16, font="F2", color=(1, 1, 1))


def draw_box(canvas: PdfCanvas, x: float, y: float, width: float, height: float, label: str) -> float:
    canvas.rect(x, y, width, height, stroke=(0.83, 0.85, 0.88), fill=(1, 1, 1))
    canvas.text(x + 14, y + height - 18, label.upper(), size=8, font="F2", color=(0.42, 0.47, 0.53))
    return y + height - 38


def draw_utility_statement(doc: UtilityStatement) -> bytes:
    canvas = PdfCanvas()
    draw_header(canvas, doc.brand, doc.subtitle, doc.accent, doc.title)

    canvas.text(48, 698, "Issued To", size=9, font="F2", color=(0.42, 0.47, 0.53))
    canvas.text(48, 682, doc.company_name, size=13, font="F2")
    current_y = 666
    for line in doc.company_address:
        canvas.text(48, current_y, line, size=10)
        current_y -= 13

    service_y = draw_box(canvas, 36, 574, 250, 96, "Service Address")
    canvas.text(50, service_y, doc.service_address, size=11, font="F2")
    canvas.text(50, service_y - 18, f"Billing Period: {doc.billing_period}", size=10)
    canvas.text(50, service_y - 34, f"Account Number: {doc.account_number}", size=10, font="F3")

    details_y = draw_box(canvas, 310, 574, 266, 96, "Statement Details")
    canvas.text(324, details_y, f"Statement Date: {doc.statement_date}", size=10)
    canvas.text(324, details_y - 18, f"Payment Due: {doc.due_date}", size=10)
    canvas.text(324, details_y - 36, "Status: Auto-pay enrolled", size=10)
    canvas.text(324, details_y - 54, "Rate Class: Commercial General Service", size=10)

    card_width = 167
    for index, (label, value, sublabel) in enumerate(doc.summary_cards):
        x = 36 + index * (card_width + 14)
        canvas.rect(x, 502, card_width, 54, stroke=(0.86, 0.88, 0.91), fill=(0.97, 0.98, 0.99))
        canvas.text(x + 14, 537, label.upper(), size=8, font="F2", color=(0.44, 0.5, 0.57))
        canvas.text(x + 14, 520, value, size=16, font="F2", color=doc.accent)
        canvas.text(x + 14, 506, sublabel, size=9, color=(0.43, 0.48, 0.54))

    canvas.rect(36, 292, 540, 186, stroke=(0.83, 0.85, 0.88), fill=(1, 1, 1))
    canvas.rect(36, 452, 540, 26, fill=(0.94, 0.96, 0.98))
    canvas.text(52, 460, "Charge Description", size=9, font="F2", color=(0.38, 0.44, 0.51))
    canvas.text(496, 460, "Amount", size=9, font="F2", color=(0.38, 0.44, 0.51))

    row_y = 430
    total = Decimal("0.00")
    for description, amount in doc.charges:
        canvas.line(48, row_y - 8, 564, row_y - 8, color=(0.9, 0.92, 0.94))
        canvas.text(52, row_y, description, size=10)
        canvas.text(480, row_y, money(amount), size=10, font="F3")
        total += amount
        row_y -= 26

    canvas.line(340, row_y - 2, 564, row_y - 2, color=doc.accent, width=1.2)
    canvas.text(392, row_y - 16, "Total Due", size=11, font="F2")
    canvas.text(480, row_y - 16, money(total), size=15, font="F2", color=doc.accent)

    note_y = draw_box(canvas, 36, 176, 540, 88, "Payment Notes")
    canvas.wrapped_text(50, note_y, doc.footer_note, max_chars=90, size=10)
    canvas.text(50, 188, "Questions? Call Commercial Billing Support at 1-800-555-0147.", size=9, color=(0.43, 0.48, 0.54))
    return canvas.render()


def draw_vendor_invoice(doc: VendorInvoice) -> bytes:
    canvas = PdfCanvas()
    draw_header(canvas, doc.brand, doc.subtitle, doc.accent, doc.title)

    bill_to_y = draw_box(canvas, 36, 574, 250, 108, "Bill To")
    canvas.text(50, bill_to_y, doc.company_name, size=13, font="F2")
    current_y = bill_to_y - 16
    for line in doc.company_address:
        canvas.text(50, current_y, line, size=10)
        current_y -= 13

    remit_y = draw_box(canvas, 310, 574, 266, 108, "Remit To")
    canvas.text(324, remit_y, doc.brand, size=13, font="F2")
    current_y = remit_y - 16
    for line in doc.vendor_address:
        canvas.text(324, current_y, line, size=10)
        current_y -= 13

    meta_y = draw_box(canvas, 36, 500, 540, 54, "Invoice Summary")
    canvas.text(50, meta_y, f"Invoice #: {doc.invoice_number}", size=10, font="F3")
    canvas.text(230, meta_y, f"Issue Date: {doc.invoice_date}", size=10)
    canvas.text(396, meta_y, f"Due Date: {doc.due_date}", size=10)
    canvas.text(50, meta_y - 18, f"Terms: {doc.terms}", size=10)

    canvas.rect(36, 252, 540, 224, stroke=(0.83, 0.85, 0.88), fill=(1, 1, 1))
    canvas.rect(36, 450, 540, 26, fill=(0.94, 0.96, 0.98))
    canvas.text(52, 458, "Description", size=9, font="F2", color=(0.38, 0.44, 0.51))
    canvas.text(388, 458, "Qty", size=9, font="F2", color=(0.38, 0.44, 0.51))
    canvas.text(444, 458, "Rate", size=9, font="F2", color=(0.38, 0.44, 0.51))
    canvas.text(510, 458, "Amount", size=9, font="F2", color=(0.38, 0.44, 0.51))

    row_y = 428
    subtotal = Decimal("0.00")
    for description, quantity, rate in doc.line_items:
        amount = rate * Decimal(quantity)
        canvas.line(48, row_y - 8, 564, row_y - 8, color=(0.9, 0.92, 0.94))
        canvas.wrapped_text(52, row_y, description, max_chars=45, size=10, line_gap=12)
        canvas.text(392, row_y, str(quantity), size=10, font="F3")
        canvas.text(438, row_y, money(rate), size=10, font="F3")
        canvas.text(502, row_y, money(amount), size=10, font="F3")
        subtotal += amount
        row_y -= 34

    canvas.rect(356, 184, 220, 56, stroke=(0.83, 0.85, 0.88), fill=(0.98, 0.99, 1))
    canvas.text(372, 222, "Subtotal", size=10)
    canvas.text(494, 222, money(subtotal), size=10, font="F3")
    canvas.text(372, 206, doc.tax_label, size=10)
    canvas.text(494, 206, money(doc.tax_amount), size=10, font="F3")
    canvas.line(372, 198, 560, 198, color=doc.accent, width=1.2)
    canvas.text(372, 186, "Amount Due", size=11, font="F2")
    canvas.text(484, 186, money(subtotal + doc.tax_amount), size=15, font="F2", color=doc.accent)

    notes_y = draw_box(canvas, 36, 98, 296, 128, "Vendor Notes")
    canvas.wrapped_text(50, notes_y, doc.notes, max_chars=46, size=10)
    canvas.text(50, 112, "Reference: Please include invoice number with remittance.", size=9, color=(0.43, 0.48, 0.54))
    return canvas.render()


def draw_fuel_receipt(doc: FuelReceipt) -> bytes:
    canvas = PdfCanvas()
    canvas.rect(132, 72, 348, 648, stroke=(0.8, 0.82, 0.86), fill=(1, 1, 1))
    canvas.rect(132, 664, 348, 56, fill=doc.accent)
    canvas.text(154, 691, doc.brand, size=18, font="F2", color=(1, 1, 1))
    canvas.text(154, 675, doc.subtitle, size=9, color=(0.94, 0.96, 0.99))
    canvas.text(154, 645, doc.company_name, size=12, font="F2")
    canvas.text(154, 628, doc.location, size=10)

    canvas.line(154, 616, 456, 616, color=(0.85, 0.87, 0.9))
    canvas.text(154, 598, f"Date: {doc.transaction_date}", size=10)
    canvas.text(312, 598, f"Time: {doc.transaction_time}", size=10)
    canvas.text(154, 580, f"Merchant ID: {doc.merchant_id}", size=10, font="F3")
    canvas.text(154, 562, f"Card Ref: {doc.card_reference}", size=10, font="F3")
    canvas.text(154, 544, f"Odometer: {doc.odometer}", size=10)

    canvas.rect(154, 330, 302, 186, stroke=(0.83, 0.85, 0.88), fill=(0.99, 0.99, 1))
    canvas.text(170, 496, "Charge Detail", size=9, font="F2", color=(0.4, 0.46, 0.52))
    canvas.text(390, 496, "Amount", size=9, font="F2", color=(0.4, 0.46, 0.52))

    row_y = 470
    running_total = Decimal("0.00")
    for description, amount in doc.line_items:
        canvas.line(166, row_y - 8, 444, row_y - 8, color=(0.91, 0.92, 0.94))
        canvas.wrapped_text(170, row_y, description, max_chars=28, size=10, line_gap=12)
        canvas.text(382, row_y, money(amount), size=10, font="F3")
        running_total += amount
        row_y -= 28

    canvas.line(170, 370, 440, 370, color=doc.accent, width=1.2)
    canvas.text(170, 350, "Total Paid", size=11, font="F2")
    canvas.text(370, 350, money(doc.total), size=16, font="F2", color=doc.accent)

    note_y = 300
    canvas.text(154, note_y, "Receipt Notes", size=9, font="F2", color=(0.42, 0.47, 0.53))
    current_y = note_y - 18
    for note in doc.notes:
        canvas.wrapped_text(154, current_y, f"- {note}", max_chars=48, size=10, line_gap=12)
        current_y -= 24

    canvas.text(154, 108, "Thank you for your business.", size=10, color=(0.43, 0.48, 0.54))
    return canvas.render()


UTILITY_STATEMENTS = [
    UtilityStatement(
        relative_path="demo_data/support_docs/maple_leaf_catering/maple_leaf_toronto_hydro_july_2024.pdf",
        brand="Toronto Hydro",
        subtitle="Commercial Energy Services",
        accent=(0.07, 0.29, 0.57),
        title="Electricity Statement",
        company_name="Maple Leaf Catering Co.",
        company_address=["Accounts Payable", "145 King St W", "Toronto, ON M5H 1J8"],
        service_address="145 King St W, Toronto, ON M5H 1J8",
        statement_date="2024-07-10",
        billing_period="2024-06-10 to 2024-07-09",
        account_number="TH-4419082",
        due_date="2024-07-25",
        summary_cards=[
            ("Usage", "13,482 kWh", "Summer production and kitchen load"),
            ("Demand", "41.2 kW", "Peak demand billed"),
            ("Amount Due", "$1,986.42", "Automatic withdrawal scheduled"),
        ],
        charges=[
            ("Energy charge", dec("1294.17")),
            ("Delivery services", dec("352.28")),
            ("Regulatory and system charge", dec("111.46")),
            ("HST", dec("228.51")),
        ],
        footer_note="This statement is a representative example of one monthly Toronto Hydro bill. It supports the optional document upload flow and does not attempt to reconcile every electricity expense in the annual CSV.",
    ),
    UtilityStatement(
        relative_path="demo_data/support_docs/maple_leaf_catering/maple_leaf_enbridge_statement_jan_2024.pdf",
        brand="Enbridge Gas",
        subtitle="Ontario Commercial Accounts",
        accent=(0.89, 0.38, 0.09),
        title="Natural Gas Statement",
        company_name="Maple Leaf Catering Co.",
        company_address=["Accounts Payable", "145 King St W", "Toronto, ON M5H 1J8"],
        service_address="145 King St W, Toronto, ON M5H 1J8",
        statement_date="2024-01-15",
        billing_period="2023-12-11 to 2024-01-10",
        account_number="EG-9931456",
        due_date="2024-01-30",
        summary_cards=[
            ("Usage", "1,842 m3", "Winter facility heating"),
            ("Rate Zone", "Toronto", "General service account"),
            ("Amount Due", "$817.64", "Due within 15 days"),
        ],
        charges=[
            ("Commodity gas charge", dec("384.22")),
            ("Delivery and storage", dec("198.55")),
            ("Transportation to Enbridge", dec("72.14")),
            ("Federal carbon charge", dec("54.75")),
            ("HST", dec("107.98")),
        ],
        footer_note="This sample gas statement represents a single winter billing cycle and is intended as a realistic support document example, not a full annual utility ledger.",
    ),
    UtilityStatement(
        relative_path="demo_data/support_docs/technorth_solutions/technorth_toronto_hydro_aug_2024.pdf",
        brand="Toronto Hydro",
        subtitle="Commercial Energy Services",
        accent=(0.07, 0.29, 0.57),
        title="Electricity Statement",
        company_name="TechNorth Solutions Inc.",
        company_address=["Finance Department", "88 Front St E", "Toronto, ON M5A 1E1"],
        service_address="88 Front St E, Toronto, ON M5A 1E1",
        statement_date="2024-08-10",
        billing_period="2024-07-10 to 2024-08-09",
        account_number="TH-7783201",
        due_date="2024-08-25",
        summary_cards=[
            ("Usage", "5,918 kWh", "Peak summer office cooling"),
            ("Demand", "18.7 kW", "Measured max demand"),
            ("Amount Due", "$814.26", "Pre-authorized payment active"),
        ],
        charges=[
            ("Energy charge", dec("525.14")),
            ("Delivery services", dec("139.77")),
            ("Regulatory and system charge", dec("55.71")),
            ("HST", dec("93.64")),
        ],
        footer_note="This is one representative Toronto Hydro statement for TechNorth Solutions. The amount is intentionally realistic but not meant to equal every utility row in the CSV.",
    ),
    UtilityStatement(
        relative_path="demo_data/support_docs/technorth_solutions/technorth_enbridge_statement_dec_2024.pdf",
        brand="Enbridge Gas",
        subtitle="Ontario Commercial Accounts",
        accent=(0.89, 0.38, 0.09),
        title="Natural Gas Statement",
        company_name="TechNorth Solutions Inc.",
        company_address=["Finance Department", "88 Front St E", "Toronto, ON M5A 1E1"],
        service_address="88 Front St E, Toronto, ON M5A 1E1",
        statement_date="2024-12-15",
        billing_period="2024-11-12 to 2024-12-11",
        account_number="EG-5528148",
        due_date="2024-12-30",
        summary_cards=[
            ("Usage", "362 m3", "Office space heating"),
            ("Rate Zone", "Toronto", "Commercial heating service"),
            ("Amount Due", "$169.42", "Online payment scheduled"),
        ],
        charges=[
            ("Commodity gas charge", dec("62.18")),
            ("Delivery and storage", dec("39.55")),
            ("Transportation to Enbridge", dec("18.76")),
            ("Federal carbon charge", dec("12.18")),
            ("HST", dec("36.75")),
        ],
        footer_note="This sample winter gas statement is designed to look like a plausible office utility bill without trying to reconcile all natural gas entries in the demo CSV.",
    ),
]


VENDOR_INVOICES = [
    VendorInvoice(
        relative_path="demo_data/support_docs/maple_leaf_catering/maple_leaf_sysco_invoice_sep_2024.pdf",
        brand="Sysco Toronto",
        subtitle="Foodservice Distribution",
        accent=(0.0, 0.38, 0.62),
        title="Supplier Invoice",
        company_name="Maple Leaf Catering Co.",
        company_address=["Accounts Payable", "145 King St W", "Toronto, ON M5H 1J8"],
        vendor_address=["Sysco Toronto", "100 Admiral Blvd", "Mississauga, ON L5T 2N1"],
        invoice_number="SY-240905-1184",
        invoice_date="2024-09-05",
        due_date="2024-09-20",
        terms="Net 15",
        line_items=[
            ("Seasonal produce and greens for event prep", 1, dec("812.45")),
            ("Protein order - poultry and braised meats", 1, dec("674.20")),
            ("Prepared desserts and dairy restock", 1, dec("438.88")),
            ("Dry goods, pantry staples, and ice", 1, dec("271.95")),
        ],
        tax_label="HST",
        tax_amount=dec("285.67"),
        notes="Representative weekly supply invoice prepared for demo uploads. Line items are intentionally realistic and align with the company profile, but they do not attempt to match every monthly food supply expense in the CSV.",
    ),
    VendorInvoice(
        relative_path="demo_data/support_docs/technorth_solutions/technorth_aws_invoice_oct_2024.pdf",
        brand="Amazon Web Services",
        subtitle="Cloud Services Billing",
        accent=(0.94, 0.55, 0.1),
        title="Services Invoice",
        company_name="TechNorth Solutions Inc.",
        company_address=["Finance Department", "88 Front St E", "Toronto, ON M5A 1E1"],
        vendor_address=["Amazon Web Services Canada", "410 Terry Ave N", "Seattle, WA 98109"],
        invoice_number="AWS-2024-10-4450",
        invoice_date="2024-10-05",
        due_date="2024-10-20",
        terms="Net 15",
        line_items=[
            ("EC2 compute workload for production services", 1, dec("628.20")),
            ("RDS database instances and backups", 1, dec("314.40")),
            ("S3 storage, requests, and data transfer", 1, dec("179.85")),
            ("Developer support plan and monitoring", 1, dec("140.00")),
        ],
        tax_label="HST",
        tax_amount=dec("164.10"),
        notes="This invoice is a polished example support document for upload testing. It is intentionally representative of a cloud billing cycle and is not expected to equal all annual services spend in the CSV.",
    ),
]


FUEL_RECEIPTS = [
    FuelReceipt(
        relative_path="demo_data/support_docs/maple_leaf_catering/maple_leaf_shell_fleet_receipt_aug_2024.pdf",
        brand="Shell Canada",
        subtitle="Fleet Card Fuel Receipt",
        accent=(0.79, 0.1, 0.12),
        company_name="Maple Leaf Catering Co.",
        location="401 Service Centre, Mississauga, ON",
        transaction_date="2024-08-20",
        transaction_time="07:42 AM",
        merchant_id="SC-1187-229",
        card_reference="Fleet Card **** 4418",
        odometer="184,233 km",
        line_items=[
            ("Ultra low sulphur diesel - 61.8 L @ $1.69/L", dec("104.44")),
            ("DEF top-up and washer fluid", dec("13.54")),
        ],
        total=dec("117.98"),
        notes=[
            "Representative single-fuel event for one delivery van.",
            "Useful for testing optional receipt uploads without recreating every fleet purchase in the CSV.",
        ],
    ),
    FuelReceipt(
        relative_path="demo_data/support_docs/technorth_solutions/technorth_petro_canada_travel_receipt_sep_2024.pdf",
        brand="Petro-Canada",
        subtitle="Travel Fuel Receipt",
        accent=(0.73, 0.09, 0.14),
        company_name="TechNorth Solutions Inc.",
        location="Calgary Downtown, AB",
        transaction_date="2024-09-15",
        transaction_time="06:18 PM",
        merchant_id="PC-8871-614",
        card_reference="Corporate Visa **** 9921",
        odometer="52,911 km",
        line_items=[
            ("Regular gasoline - 36.4 L @ $1.67/L", dec("60.79")),
            ("Station service fee and taxes", dec("12.46")),
        ],
        total=dec("73.25"),
        notes=[
            "Example client-trip travel receipt tied to a single field visit.",
            "Amount is intentionally realistic but is not meant to reconcile the full annual travel category.",
        ],
    ),
]


def write_document(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    print(path)


def main() -> None:
    root = Path(__file__).resolve().parent.parent

    for doc in UTILITY_STATEMENTS:
        write_document(root / doc.relative_path, draw_utility_statement(doc))

    for doc in VENDOR_INVOICES:
        write_document(root / doc.relative_path, draw_vendor_invoice(doc))

    for doc in FUEL_RECEIPTS:
        write_document(root / doc.relative_path, draw_fuel_receipt(doc))


if __name__ == "__main__":
    main()
