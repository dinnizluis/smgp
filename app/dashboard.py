import sys
from pathlib import Path

# Ensure project root is on sys.path so top-level packages (importers, infrastructure)
# resolve when Streamlit runs `app/dashboard.py` as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

import streamlit as st
import altair as alt
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

			# prepare chart and table data: compute magnitude and pct, then sort both
			try:
				_chart_df = df_cat.copy()
				_chart_df['abs_total'] = _chart_df['total'].abs()
				_chart_df = _chart_df.sort_values('abs_total', ascending=False)
				# total magnitude across visible categories (for pct calculation)
				total_magnitude = _chart_df['abs_total'].sum()
				if total_magnitude > 0:
					# pct as fraction (0.0 - 1.0) so Altair's percent formatting works
					_chart_df['pct'] = (_chart_df['abs_total'] / total_magnitude)
				else:
					_chart_df['pct'] = 0.0

				# map pct and abs_total back into df_cat so the displayed table matches the chart
				pct_map = dict(zip(_chart_df['category'], _chart_df['pct']))
				abs_map = dict(zip(_chart_df['category'], _chart_df['abs_total']))
				df_cat['abs_total'] = df_cat['category'].map(abs_map).fillna(0)
				df_cat['pct'] = df_cat['category'].map(pct_map)

				# sort df_cat by magnitude descending for display
				df_cat = df_cat.sort_values('abs_total', ascending=False).reset_index(drop=True)

				# select top N for chart (default 8)
				_chart_top = _chart_df.head(8)
				# build Altair chart to preserve ordering by abs_total
				_chart_top = _chart_top.copy()
				_chart_top = _chart_top.reset_index(drop=True)
				chart_df = _chart_top[['category', 'total', 'pct', 'abs_total']]
				st.subheader('Gastos por categoria (gráfico)')
				# allow switching between absolute values and percentage view
				chart_mode = st.radio('Exibir gráfico como', ['Valores', 'Porcentagem (%)'], index=0, horizontal=True)
				if chart_mode == 'Porcentagem (%)':
					# show pct on Y axis
					chart = alt.Chart(chart_df).mark_bar().encode(
						x=alt.X('category:N', sort=alt.SortField('abs_total', order='descending')),
						y=alt.Y('pct:Q', axis=alt.Axis(format='%')), 
						tooltip=[alt.Tooltip('category:N'), alt.Tooltip('pct:Q', format='.2f')],
					).properties(width=800)
				else:
					chart = alt.Chart(chart_df).mark_bar().encode(
						x=alt.X('category:N', sort=alt.SortField('abs_total', order='descending')),
						y=alt.Y('total:Q'),
						tooltip=[alt.Tooltip('category:N'), alt.Tooltip('total:Q', format='.2f'), alt.Tooltip('pct:Q', format='.2f')],
					).properties(width=800)
				st.altair_chart(chart, use_container_width=True)
			except Exception:
				# do not break UI if chart generation fails; keep original df_cat
				pass

			# append total row for display (sum of visible categories)
			total_sum = df_cat['total'].sum()
			total_row = _pd.DataFrame([{"category": "Total", "total": total_sum, "pct": 1.0}])
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
		# format pct column for display (convert fraction to percentage string)
		if 'pct' in df_cat.columns:
			df_cat['pct'] = df_cat['pct'].apply(lambda v: f"{(v or 0.0)*100:.2f}%")
		st.dataframe(df_cat)

		# --- Gerenciar categorização (MVP) -------------------------------------------------
		with st.expander("Gerenciar categorização", expanded=False):
			st.write("Ajuste manual de categorias para transações no período selecionado.")
			only_uncat = st.checkbox("Somente Não categorizado", value=True)
			# load transactions in the period (limited recent rows for performance)
			tx_repo = TransactionRepository()
			cat_repo = CategoryRepository()
			# ensure we know the canonical id for the default 'Não categorizado' category
			default_cat_id = cat_repo.ensure(None, "Não categorizado")
			all_txs = tx_repo.list_all(limit=1000)
			# filter by date range — normalize to date objects to handle DB types
			from datetime import datetime
			def _to_date(d):
				if isinstance(d, date):
					return d
				try:
					return datetime.fromisoformat(str(d)).date()
				except Exception:
					return None
			start_dt = datetime.fromisoformat(start_iso).date()
			end_dt = datetime.fromisoformat(end_iso).date()
			visible = [t for t in all_txs if (_to_date(t.get('date')) is not None and _to_date(t.get('date')) >= start_dt and _to_date(t.get('date')) <= end_dt)]
			if only_uncat:
				# consider transactions uncategorized when they have no category_id OR
				# when their category_id equals the default 'Não categorizado' id
				visible = [t for t in visible if (not t.get('category_id')) or (t.get('category_id') == default_cat_id)]

			if not visible:
				st.info('Nenhuma transação encontrada para o período e filtro selecionado.')
			else:
				# load categories for select options
				cats = cat_repo.list_all()
				cat_options = [c['name'] for c in cats]
				cat_options.insert(0, 'Não categorizado')
				cat_options.append('Criar nova categoria...')

				# collect selections in session state keys to preserve across reruns
				selections = {}
				new_names = {}
				st.write('Selecione a nova categoria para cada transação e clique em Salvar alterações.')
				for t in visible:
					row_id = t['id']
					cols = st.columns([1, 3, 2, 2])
					with cols[0]:
						st.write(t['date'])
					with cols[1]:
						st.write(t['description'])
					with cols[2]:
						st.write(f"{t['amount']:.2f}")
					with cols[3]:
						key = f"cat_select_{row_id}"
						# determine current category name
						current_name = 'Não categorizado'
						if t.get('category_id'):
							c = cat_repo.list_all()
							cm = {c2['id']: c2['name'] for c2 in c}
							current_name = cm.get(t.get('category_id'), 'Não categorizado')
						sel = st.selectbox('', options=cat_options, index=cat_options.index(current_name) if current_name in cat_options else 0, key=key)
						selections[row_id] = sel
						# if create new chosen, show input
						if sel == 'Criar nova categoria...':
							nkey = f"cat_new_{row_id}"
							new = st.text_input('Nome da nova categoria', key=nkey)
							new_names[row_id] = new

				if st.button('Salvar alterações'):
					applied = 0
					for tx_id, sel in selections.items():
						if sel == 'Criar nova categoria...':
							name = new_names.get(tx_id)
							if not name:
								continue
							cat_id = cat_repo.ensure(None, name)
						elif sel == 'Não categorizado':
							cat_id = None
						else:
							# find id by name
							c = cat_repo.list_all()
							cm = {c2['name']: c2['id'] for c2 in c}
							cat_id = cm.get(sel)
						# apply update
						ok = tx_repo.update_category(tx_id, cat_id)
						if ok:
							applied += 1
					st.success(f"Categorias atualizadas: {applied}")
					# refresh page to show new values
					st.experimental_rerun()
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
