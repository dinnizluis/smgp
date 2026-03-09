from __future__ import annotations

from typing import List, Union, IO
import re
from io import BytesIO
from domain.models import Transaction


class InvalidPDFError(Exception):
    pass


def parse_nubank_pdf(file: Union[str, IO, bytes]) -> List[Transaction]:
    """Parse a Nubank PDF statement (heuristic) and return Transactions.

    Nubank PDFs usually contain lines with a date and a description followed by
    an amount. This is a lightweight heuristic parser sufficient for MVP.
    """
    if isinstance(file, (bytes, bytearray)):
        fh = BytesIO(file)
    else:
        fh = file

    try:
        import pdfplumber
    except Exception:
        raise InvalidPDFError("Dependência pdfplumber não encontrada. Instale via 'pip install pdfplumber'")

    try:
        with pdfplumber.open(fh) as pdf:
            text_lines = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                for ln in text.splitlines():
                    text_lines.append(ln.strip())
    except Exception as exc:
        raise InvalidPDFError(f"Erro lendo PDF: {exc}") from exc

    date_re = re.compile(r"(\d{2}/\d{2}/\d{4}|\d{2}/\d{2})")
    amt_re = re.compile(r"(-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))")

    rows: List[Transaction] = []
    for ln in text_lines:
        if 'Lançamentos' in ln or 'Extrato' in ln:
            continue
        dmatch = date_re.search(ln)
        amatch = amt_re.search(ln)
        if dmatch and amatch:
            raw_date = dmatch.group(1)
            try:
                from datetime import datetime
                if raw_date.count('/') == 1:
                    year = datetime.now().year
                    dt = datetime.strptime(f"{raw_date}/{year}", "%d/%m/%Y")
                else:
                    dt = datetime.strptime(raw_date, "%d/%m/%Y")
                date_iso = dt.date().isoformat()
            except Exception:
                continue

            raw_amt = amatch.group(1)
            a = raw_amt.replace("R$", "").replace("$", "").strip()
            if a.count(',') and a.count('.'):
                if a.rfind('.') > a.rfind(','):
                    a = a.replace(',', '')
                else:
                    a = a.replace('.', '').replace(',', '.')
            elif ',' in a:
                a = a.replace('.', '').replace(',', '.')
            a = a.replace(' ', '')
            try:
                val = float(a)
            except Exception:
                continue

            desc = ln
            desc = date_re.sub('', desc)
            desc = amt_re.sub('', desc)
            desc = desc.strip(' -–—\t\n')

            tx = Transaction(id=None, date=date_iso, description=desc or 'Descrição', amount=val)
            rows.append(tx)

    return rows
