from __future__ import annotations

from typing import List, Union, IO
import re
from io import BytesIO
from domain.models import Transaction


class InvalidPDFError(Exception):
    pass


def parse_itau_pdf(file: Union[str, IO, bytes]) -> List[Transaction]:
    """Parse an Itaú card statement PDF and return list of Transactions.

    This is a heuristic parser that extracts lines containing a date and an
    amount. It returns transactions with ISO date strings and float amounts.
    """
    # load bytes into pdfplumber
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

    # simple heuristics: look for lines with date (dd/mm or dd/mm/yyyy) and amount
    date_re = re.compile(r"(\d{2}/\d{2}(?:/\d{2,4})?)")
    amt_re = re.compile(r"(-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))")

    rows: List[Transaction] = []
    for ln in text_lines:
        # try to find both date and amount on the same line
        dmatch = date_re.search(ln)
        amatch = None
        # sometimes amount appears at end of line
        parts = ln.rsplit(" ", 3)
        for p in parts:
            m = amt_re.search(p)
            if m:
                amatch = m
                break
        if dmatch and amatch:
            raw_date = dmatch.group(1)
            # normalize date (assume current year if two-digit day/month only)
            try:
                from datetime import datetime

                if raw_date.count("/") == 1:
                    # dd/mm -> try current year
                    year = datetime.now().year
                    dt = datetime.strptime(f"{raw_date}/{year}", "%d/%m/%Y")
                else:
                    dt = datetime.strptime(raw_date, "%d/%m/%Y")
                date_iso = dt.date().isoformat()
            except Exception:
                continue

            raw_amt = amatch.group(1)
            # normalize amount string like 1.234,56 or 1,234.56
            a = raw_amt.replace("R$", "").replace("$", "").strip()
            if a.count(",") and a.count("."):
                if a.rfind(".") > a.rfind(","):
                    a = a.replace(",", "")
                else:
                    a = a.replace(".", "").replace(",", ".")
            elif "," in a:
                a = a.replace(".", "").replace(",", ".")
            a = a.replace(" ", "")
            try:
                val = float(a)
            except Exception:
                continue

            # description: remove date and amount parts
            desc = ln
            desc = date_re.sub("", desc)
            desc = amt_re.sub("", desc)
            desc = desc.strip(" -–—\t\n")

            tx = Transaction(id=None, date=date_iso, description=desc or "Descrição", amount=val)
            rows.append(tx)

    return rows
