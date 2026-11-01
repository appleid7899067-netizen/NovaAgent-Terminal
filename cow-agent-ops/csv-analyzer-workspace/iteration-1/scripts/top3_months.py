#!/usr/bin/env python3
import argparse
import csv
import os
from collections import defaultdict


def detect_columns(header):
    h = [str(x).strip().lower() for x in header]
    month_keys = ['month','date','period','period_name','month_name']
    revenue_keys = ['revenue','sales','amount','value','total','profit']
    month_idx = next((i for i, v in enumerate(h) if v in month_keys), None)
    rev_idx = next((i for i, v in enumerate(h) if v in revenue_keys), None)
    if month_idx is None:
        month_idx = 0
    if rev_idx is None:
        rev_idx = 1 if len(header) > 1 else None
    return month_idx, rev_idx


def main():
    parser = argparse.ArgumentParser(description='Top-3 months by revenue from a CSV and output a summary plus a bar chart.')
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--output', default=None, help='Output directory for results')
    args = parser.parse_args()

    input_path = args.input
    if not os.path.exists(input_path):
        print(f'ERROR: Input CSV not found: {input_path}')
        raise SystemExit(2)

    with open(input_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            print('ERROR: CSV is empty')
            raise SystemExit(3)
        month_idx, rev_idx = detect_columns(header)
        totals = defaultdict(float)
        for row in reader:
            if not row:
                continue
            m = row[month_idx] if month_idx < len(row) else ''
            v = row[rev_idx] if rev_idx is not None and rev_idx < len(row) else '0'
            try:
                val = float(v)
            except:
                continue
            totals[m] += val

    # Top 3 months by revenue
    items = sorted([(k, v) for k, v in totals.items() if k], key=lambda x: x[1], reverse=True)[:3]

    out_dir = args.output or 'csv-analyzer-workspace/iteration-1/eval-top-months-chart/with_skill/outputs'
    os.makedirs(out_dir, exist_ok=True)

    summary_path = os.path.join(out_dir, 'top3_months_summary.csv')
    with open(summary_path, 'w', newline='', encoding='utf-8') as sf:
        w = csv.writer(sf)
        w.writerow(['Month','Revenue'])
        for m, rv in items:
            w.writerow([m, rv])

    # Optional chart generation
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        months = [m for m, _ in items]
        revs = [rv for _, rv in items]
        plt.figure(figsize=(6,4))
        plt.bar(months, revs, color='royalblue')
        plt.xlabel('Month')
        plt.ylabel('Revenue')
        plt.title('Top 3 Months by Revenue')
        plt.tight_layout()
        chart_path = os.path.join(out_dir, 'top3_months_bar_chart.png')
        plt.savefig(chart_path, dpi=300)
        print(f'OUTPUTS GENERATED: summary={summary_path}, chart={chart_path}')
    except Exception as e:
        # If matplotlib is not available, still provide summary
        print(f'NOTE: Chart could not be generated: {e}')
        print(f'OUTPUTS GENERATED: summary={summary_path} (no chart)')

    print('DONE')


if __name__ == '__main__':
    main()
