from datetime import datetime

def build_html(total_cost, top_services, daily_costs, waste_items, anomaly_count):
    labels = [d['date'] for d in daily_costs]
    costs = [d['cost'] for d in daily_costs]
    
    # Convert lists to JS strings
    labels_js = str(labels).replace("'", '"')
    costs_js = str(costs)

    svc_rows = ''.join([
        f'<tr><td>{s["service"]}</td><td>${s["cost"]:.2f}</td></tr>'
        for s in top_services
    ])

    waste_total = sum(w.get('monthly_cost', 0) for w in waste_items)
    waste_rows = ''.join([
        f'<tr><td>{w["resource_type"]}</td><td>{w["resource_id"]}</td><td>${w.get("monthly_cost",0):.2f}</td><td>{w["reason"]}</td></tr>'
        for w in waste_items
    ]) if waste_items else '<tr><td colspan="4">No waste detected</td></tr>'

    generated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CostGuard Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: sans-serif; margin: 40px; background: #f4f7f6; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; }}
            .stat {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .danger {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>CostGuard Dashboard</h1>
            <p>Last updated: {generated_at}</p>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Monthly Spend (Last 30 Days)</h3>
                <p class="stat">${total_cost:.2f}</p>
                <canvas id="costChart"></canvas>
            </div>
            <div class="card">
                <h3>Top 5 Services</h3>
                <table>
                    <tr><th>Service</th><th>Cost</th></tr>
                    {svc_rows}
                </table>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Recoverable Waste</h3>
                <p class="stat danger">${waste_total:.2f}/mo</p>
                <table>
                    <tr><th>Type</th><th>ID</th><th>Cost/mo</th><th>Reason</th></tr>
                    {waste_rows}
                </table>
            </div>
            <div class="card">
                <h3>Anomalies Detected</h3>
                <p class="stat {"danger" if anomaly_count > 0 else ""}">{anomaly_count}</p>
                <p>Spikes > 20% compared to 7-day average.</p>
            </div>
        </div>

        <script>
            new Chart(document.getElementById('costChart'), {{
                type: 'line',
                data: {{
                    labels: {labels_js},
                    datasets: [{{
                        label: 'Daily Spend ($)',
                        data: {costs_js},
                        borderColor: '#3498db',
                        fill: false
                    }}]
                }}
            }});
        </script>
    </body>
    </html>
    '''
