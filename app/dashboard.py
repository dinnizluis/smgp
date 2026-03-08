import sys
from pathlib import Path

# Ensure project root is on sys.path so top-level packages (importers, infrastructure)
# resolve when Streamlit runs `app/dashboard.py` as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

import streamlit as st
from importers.csv_importer import parse_csv, InvalidCSVError
from infrastructure.repositories import TransactionRepository, CategoryRepository, ImportBatchRepository, bootstrap
import uuid
import pandas as pd


st.title("Sistema de Monitoramento de Gastos Pessoais")


def main():
	st.write("Importar transações via CSV")

	uploaded = st.file_uploader("Escolha um arquivo CSV", type=["csv"])

	if uploaded is not None:
		try:
			rows = parse_csv(uploaded)
		except InvalidCSVError as e:
			st.error(f"Arquivo inválido: {e}")
			return

		# rows is a list of Transaction dataclasses — convert to dicts for display
		df = pd.DataFrame([{
			"date": t.date,
			"description": t.description,
			"amount": t.amount,
		} for t in rows])
		st.subheader("Pré-visualização")
		st.dataframe(df)

		st.markdown(f"**Linhas detectadas:** {len(rows)}")

		if st.button("Persistir transações"):
			# ensure DB and default category
			bootstrap()
			tx_repo = TransactionRepository()
			cat_repo = CategoryRepository()
			default_cat = cat_repo.ensure(None, "Não categorizado")

			# create import batch metadata (minimal)
			batch_repo = ImportBatchRepository()
			batch_id = uuid.uuid4().hex
			source = getattr(uploaded, "name", "upload_streamlit")
			try:
				batch_repo.create_batch(batch_id, source=source)
			except Exception:
				# fail-safe: don't block persistence if batch metadata fails
				batch_id = None

			inserted = 0
			skipped = 0
			for t in rows:
				ok = tx_repo.insert(date=t.date, description=t.description, amount=t.amount, account_type=t.account_type or "checking", category_id=default_cat)
				if ok:
					inserted += 1
				else:
					skipped += 1

			# update batch counts if created
			if batch_id:
				try:
					batch_repo.update_counts(batch_id, rows_parsed=len(rows), inserted=inserted, failed=skipped)
				except Exception:
					pass

			st.success(f"Persistido: {inserted} — Ignorados (duplicados): {skipped}")


if __name__ == "__main__":
	main()
