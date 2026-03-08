from __future__ import annotations

from typing import List, IO, Union
import pandas as pd
from datetime import datetime
from domain.models import Transaction


class InvalidCSVError(Exception):
	pass


def parse_csv(file: Union[str, IO, bytes]) -> List[Transaction]:
	"""Parse CSV and return list of transaction dicts with keys:
	date (ISO str), description (str), amount (float)

	Accepts file path, file-like object (Streamlit upload) or bytes.
	Raises InvalidCSVError if required columns are missing or parsing fails.
	"""
	# Read with pandas (handles bytes/file-like/path)
	try:
		if isinstance(file, (bytes, bytearray)):
			from io import BytesIO

			df = pd.read_csv(BytesIO(file))
		else:
			df = pd.read_csv(file)
	except Exception as exc:
		raise InvalidCSVError(f"Erro ao ler CSV: {exc}") from exc

	# map common column name variants to the canonical keys
	cols = {c.lower(): c for c in df.columns}

	def find_col(candidates):
		for c in candidates:
			if c in cols:
				return cols[c]
		return None

	date_col = find_col(["date", "data"])
	desc_col = find_col(["description", "descrição", "descricao", "title", "titulo", "name"]) 
	amount_col = find_col(["amount", "valor", "value"])

	missing = []
	if date_col is None:
		missing.append("date")
	if desc_col is None:
		missing.append("description/title")
	if amount_col is None:
		missing.append("amount")
	if missing:
		raise InvalidCSVError(f"CSV faltando colunas obrigatórias: {', '.join(missing)}")

	# work with original column names

	rows: List[Transaction] = []
	for _, r in df.iterrows():
		try:
			# parse date to ISO (YYYY-MM-DD)
			raw_date = r.get(date_col)
			if pd.isna(raw_date):
				raise ValueError("date vazio")
			# try pandas to_datetime for flexibility
			dt = pd.to_datetime(raw_date)
			date_iso = dt.date().isoformat()

			desc_raw = r.get(desc_col, "")
			if pd.isna(desc_raw):
				raise ValueError("description vazio")
			desc = str(desc_raw).strip()
			if desc == "":
				raise ValueError("description vazio")

			amt_raw = r.get(amount_col)
			if pd.isna(amt_raw):
				raise ValueError("amount vazio")
			# clean amount (remove currency symbols / thousand separators)
			if isinstance(amt_raw, str):
				a = amt_raw.replace("R$", "").replace("$", "").replace(".", "").replace(",", ".")
				amount = float(a)
			else:
				amount = float(amt_raw)

			tx = Transaction(
				id=None,
				date=date_iso,
				description=desc,
				amount=amount,
			)
			rows.append(tx)
		except Exception as exc:
			raise InvalidCSVError(f"Erro ao parsear linha: {exc}") from exc

	return rows

