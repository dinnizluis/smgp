import sys
from pathlib import Path

# Ensure project root is on sys.path so top-level packages (importers, infrastructure)
# resolve when Streamlit runs `app/dashboard.py` as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

import streamlit as st
from importers.csv_importer import parse_csv, InvalidCSVError
from infrastructure.repositories import TransactionRepository, CategoryRepository, bootstrap
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

			inserted = 0
			skipped = 0
			for t in rows:
				ok = tx_repo.insert(date=t.date, description=t.description, amount=t.amount, account_type=t.account_type or "checking", category_id=default_cat)
				if ok:
					inserted += 1
				else:
					skipped += 1

			st.success(f"Persistido: {inserted} — Ignorados (duplicados): {skipped}")


if __name__ == "__main__":
	main()
