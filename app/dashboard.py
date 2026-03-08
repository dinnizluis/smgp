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
from application.use_cases import get_week_comparison, get_category_totals_current_week
import uuid
import pandas as pd


st.title("Sistema de Monitoramento de Gastos Pessoais")


def file_type_to_account_type(label: str) -> str:
	"""Map UI label to account_type value."""
	if label == "Fatura cartão":
		return "credit"
	return "checking"


def guess_account_type(name: str) -> str:
	if not name:
		return "checking"
	low = name.lower()
	credit_keywords = ["credit", "cartao", "cartão", "creditcard", "nubank", "visa", "master", "amex"]
	for k in credit_keywords:
		if k in low:
			return "credit"
	return "checking"


def main():
	st.write("Importar transações via CSV")

	uploaded = st.file_uploader("Escolha um arquivo CSV", type=["csv"])

	if uploaded is not None:
		try:
			rows = parse_csv(uploaded)
		except InvalidCSVError as e:
			st.error(f"Arquivo inválido: {e}")
			return

		# file type dropdown: explicit choice if file is checking account or credit card invoice
		guessed = guess_account_type(getattr(uploaded, "name", ""))
		# map guessed account to label for preselection
		guessed_label = "Fatura cartão" if guessed == "credit" else "Conta corrente"
		selected_file_type = st.selectbox("Tipo de arquivo", ["Conta corrente", "Fatura cartão"], index=0 if guessed_label=="Conta corrente" else 1)
		selected_account_type = file_type_to_account_type(selected_file_type)

		# rows is a list of Transaction dataclasses — convert to dicts for display
		# show selected account type in preview (always reflect user's selection)
		df = pd.DataFrame([{
			"date": t.date,
			"description": t.description,
			"amount": t.amount,
			"account_type": selected_account_type,
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
			# apply selected account type to rows before persisting (override defaults)
			for t in rows:
				t.account_type = selected_account_type
				ok = tx_repo.insert(date=t.date, description=t.description, amount=t.amount, account_type=selected_account_type, category_id=default_cat)
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

	# show weekly consolidation
	try:
		summary = get_dashboard_summary()
		st.subheader("Resumo semanal")
		st.metric("Semana atual", f"{summary['current']:.2f}")
		pct = summary.get('pct_change')
		if pct is None:
			st.write("Sem dados da semana anterior para comparação")
		else:
			st.metric("Variação vs semana anterior", f"{pct}%")

		st.subheader("Gastos por categoria (semana atual)")
		import pandas as _pd
		df_cat = _pd.DataFrame(summary.get('categories', []))
		st.dataframe(df_cat)
	except Exception:
		# keep UI resilient if summary computation fails
		pass


def get_dashboard_summary(db_path: str = None):
    """Return a serializable dict with weekly consolidation for UI and tests.

    Keys: current, previous, pct_change, categories (list of {category, total}).
    """
    comp = get_week_comparison(db_path)
    cats = get_category_totals_current_week(db_path)
    return {"current": comp["current"], "previous": comp["previous"], "pct_change": comp["pct_change"], "categories": cats}


if __name__ == "__main__":
	main()
