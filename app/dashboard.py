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
from application.use_cases import (
	get_week_comparison,
	get_category_totals_current_week,
	infer_category_for_transaction,
	load_category_rules,
	_week_start_end_for,
	get_period_total,
	get_period_category_totals,
	compute_period_preset,
)
import uuid
import pandas as pd
from datetime import date


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

			# load category rules (if any) to suggest categories during import
			rules = load_category_rules()

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
				# try to infer a category name, map to id, fallback to default
				cat_name = infer_category_for_transaction(t, rules)
				if cat_name:
					try:
						cat_id = cat_repo.ensure(None, cat_name)
					except Exception:
						cat_id = default_cat
				else:
					cat_id = default_cat
				ok = tx_repo.insert(date=t.date, description=t.description, amount=t.amount, account_type=selected_account_type, category_id=cat_id)
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
		# allow user to choose a custom period; default is current ISO week
		# presets
		preset = st.selectbox("Período pré-definido", ["Custom", "current_week", "last_4_weeks", "last_month", "last_quarter", "last_6_months", "last_year"], index=1)
		if preset != "Custom":
			ps, pe = compute_period_preset(preset)
			start_input = pd.to_datetime(ps).date()
			end_input = pd.to_datetime(pe).date()
		else:
			week_start, week_end = _week_start_end_for(date.today())
			start_input, end_input = st.date_input("Período (início, fim)", value=(pd.to_datetime(week_start).date(), pd.to_datetime(week_end).date()))
		# normalize to ISO strings
		start_iso = start_input.isoformat()
		end_iso = end_input.isoformat()
		summary = get_dashboard_summary(db_path=None, start_date=start_iso, end_date=end_iso)

		# UI option: include uncategorized in displayed totals
		include_uncat = st.checkbox("Incluir 'Não categorizado' nos totais", value=True)

		st.subheader("Resumo de gastos")
		st.metric("Período", f"{summary['period_start']} → {summary['period_end']}")

		# compute displayed category table according to toggles
		import pandas as _pd
		df_cat = _pd.DataFrame(summary.get('categories', []))
		if df_cat.empty:
			st.dataframe(df_cat)
		else:
			# filter uncategorized if requested
			if not include_uncat:
				df_cat = df_cat[df_cat['category'] != 'Não categorizado']

			# adjust sign for display: income categories -> positive, others -> negative
			income_keywords = ['renda', 'salario', 'salário', 'receita']
			def adjust_total(row):
				cat = str(row['category']).lower()
				tot = float(row['total'])
				if any(k in cat for k in income_keywords):
					# show income as positive
					return abs(tot)
				# show expenses as negative for clarity
				return -abs(tot)

			df_cat['total'] = df_cat.apply(adjust_total, axis=1)

			# prepare chart data: sort by absolute value (magnitude) and take top N (8)
			try:
				_chart_df = df_cat.copy()
				_chart_df['abs_total'] = _chart_df['total'].abs()
				_chart_df = _chart_df.sort_values('abs_total', ascending=False)
				_chart_top = _chart_df.head(8)
				# use the signed `total` for the chart so incomes remain positive and
				# expenses appear negative; ordering is by magnitude
				chart_series = _chart_top.set_index('category')['total']
				st.subheader('Gastos por categoria (gráfico)')
				st.bar_chart(chart_series)
			except Exception:
				# do not break UI if chart generation fails
				pass

			# append total row for display (sum of visible categories)
			total_sum = df_cat['total'].sum()
			total_row = _pd.DataFrame([{"category": "Total", "total": total_sum}])
			df_cat = _pd.concat([df_cat, total_row], ignore_index=True)
			st.metric("Total (período)", f"{total_sum:.2f}")

			# compute previous period displayed totals for percentage change
			from datetime import datetime, timedelta
			sd = datetime.fromisoformat(start_iso).date()
			ed = datetime.fromisoformat(end_iso).date()
			length = (ed - sd).days + 1
			prev_s = (sd - timedelta(days=length)).isoformat()
			prev_e = (ed - timedelta(days=length)).isoformat()
			prev_cats = get_period_category_totals(prev_s, prev_e)
			prev_df = _pd.DataFrame(prev_cats)
			if not prev_df.empty:
				if not include_uncat:
					prev_df = prev_df[prev_df['category'] != 'Não categorizado']
				# apply same display rule to previous period
				prev_df['total'] = prev_df.apply(lambda r: abs(r['total']) if any(k in str(r['category']).lower() for k in income_keywords) else -abs(r['total']), axis=1)
				prev_total = prev_df['total'].sum()
			else:
				prev_total = 0.0

			if prev_total == 0:
				st.write("Sem dados do período anterior para comparação")
			else:
				pct = round((total_sum - prev_total) / abs(prev_total) * 100, 2)
				st.metric("Variação vs período anterior", f"{pct}%")

		st.subheader("Gastos por categoria (período)")
		st.dataframe(df_cat)
	except Exception:
		# keep UI resilient if summary computation fails
		pass


def get_dashboard_summary(db_path: str = None, start_date: str = None, end_date: str = None):
	"""Return a serializable dict with consolidation for UI and tests.

	Default behavior (no start/end) uses the current ISO week. Returns keys:
	- period_start, period_end: ISO date strings for the period used
	- current: total for the period
	- previous: total for the previous period (same length)
	- pct_change: percent change or None
	- categories: list of {category, total}
	"""
	# determine period
	if start_date and end_date:
		s, e = start_date, end_date
	else:
		s, e = _week_start_end_for(date.today())

	# current period totals
	current_total = get_period_total(s, e, db_path)
	cats = get_period_category_totals(s, e, db_path)

	# previous period of same length
	from datetime import datetime
	from datetime import timedelta
	sd = datetime.fromisoformat(s).date()
	ed = datetime.fromisoformat(e).date()
	length = (ed - sd).days + 1
	prev_start = sd - timedelta(days=length)
	prev_end = ed - timedelta(days=length)
	previous_total = get_period_total(prev_start.isoformat(), prev_end.isoformat(), db_path)

	if previous_total == 0:
		pct = None
	else:
		pct = round((current_total - previous_total) / abs(previous_total) * 100, 2)

	return {
		"period_start": s,
		"period_end": e,
		"current": current_total,
		"previous": previous_total,
		"pct_change": pct,
		"categories": cats,
	}


if __name__ == "__main__":
	main()
