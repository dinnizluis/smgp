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
			date_iso = _normalize_date(raw_date)

			desc_raw = r.get(desc_col, "")
			desc = _normalize_description(desc_raw)

			amt_raw = r.get(amount_col)
			amount = _normalize_amount(amt_raw)

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


def _normalize_amount(amt_raw) -> float:
	if pd.isna(amt_raw):
		raise ValueError("amount vazio")

	# numeric-like
	if isinstance(amt_raw, (int, float)):
		return float(amt_raw)

	# string: remove currency symbols and thousand separators
	if isinstance(amt_raw, str):
		a = amt_raw.replace("R$", "").replace("$", "").strip()
		# both separators present: decide by last occurrence which is decimal
		if "," in a and "." in a:
			if a.rfind(".") > a.rfind(","):
				# dot is decimal, remove comma thousands
				a = a.replace(",", "")
			else:
				# comma is decimal, remove dots and replace comma
				a = a.replace(".", "").replace(",", ".")
		# only comma present -> assume comma is decimal
		elif "," in a:
			a = a.replace(".", "").replace(",", ".")
		# only dot present -> leave as-is (may be decimal or thousand sep without comma)
		# remove spaces
		a = a.replace(" ", "")
		return float(a)

	raise ValueError("amount inválido")


def _normalize_date(raw_date) -> str:
	if pd.isna(raw_date):
		raise ValueError("date vazio")
	# use pandas flexible parser
	try:
		dt = pd.to_datetime(raw_date)
		return dt.date().isoformat()
	except Exception as exc:
		raise ValueError(f"date inválida: {exc}") from exc


def _normalize_description(raw_desc) -> str:
	if pd.isna(raw_desc):
		raise ValueError("description vazio")
	d = str(raw_desc).strip()
	if d == "":
		raise ValueError("description vazio")
	return d

