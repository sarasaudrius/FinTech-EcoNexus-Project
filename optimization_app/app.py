'''
App module for the optimization app.
'''

from flask import Flask, request, render_template, redirect, url_for, flash, session
import os
import pandas as pd
import gurobipy as gp
import matplotlib.pyplot as plt
import io
import base64
import plotly as plotly
import plotly.graph_objects as go
from gurobipy import GRB
from celery import Celery
from plotly.io import to_json
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Ensure the uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            return redirect(url_for('set_weights', filename=file.filename))
    return render_template('upload.html')

@app.route('/weights/<filename>', methods=['GET', 'POST'])
def set_weights(filename):
    if request.method == 'POST':
        total_demand = float(request.form['total_demand'])
        weights = {
            'cost': float(request.form['weight_cost']),
            'water': float(request.form['weight_water'])
        }
        goals = {
            'cost': float(request.form['cost_goal']),
            'water': float(request.form['water_goal'])
        }
        yield_scenario = 'average'

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(filepath)
        result = optimize(df, total_demand, weights, goals, yield_scenario)

        session['weights'] = weights
        session['goals'] = goals
        session['total_demand'] = total_demand

        return render_template('results.html', result=result)
    return render_template('weights.html', filename=filename)

@app.route('/scenario/<filename>/<scenario>', methods=['GET'])
def show_scenario(filename, scenario):
    print(f"Filename: {filename}, Scenario: {scenario}")  # Debugging output
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return "File not found", 404
    
    df = pd.read_csv(filepath)

    weights = session.get('weights')
    goals = session.get('goals')
    total_demand = session.get('total_demand')

    if weights is None or goals is None or total_demand is None:
        flash("Session data is missing, please re-upload the file and set weights.")
        return redirect(url_for('index'))

    result = optimize(df, total_demand, weights, goals, scenario)
    result['filename'] = filename  # Ensure filename is passed to the template
    return render_template('results.html', result=result)

@celery.task
def optimize(df, total_demand, weights, goals, yield_scenario):
    suppliers = df['Supplier ID']
    cost_per_bag = df['Cost per bag (euros)']
    water_usage = df['Water usage (liters per bag)']
    farm_size = df['Farm size (ha)']
    yield_per_ha = df['Yield (bags per ha)']

    if yield_scenario == 'high':
        yield_per_ha = [y * 1.2 for y in yield_per_ha]  # 20% higher than average
    elif yield_scenario == 'low':
        yield_per_ha = [y * 0.8 for y in yield_per_ha]  # 20% lower than average

    supply_capacity = [int(farm_size[i] * yield_per_ha[i]) for i in range(len(suppliers))]

    model = gp.Model("supplier_selection")

    x = model.addVars(suppliers, vtype=GRB.INTEGER, name="x", lb=0)
    deviation_vars = {
        'cost': (model.addVar(name="d_cost_plus", lb=0), model.addVar(name="d_cost_minus", lb=0)),
        'water': (model.addVar(name="d_water_plus", lb=0), model.addVar(name="d_water_minus", lb=0))
    }

    model.setObjective(
        weights['cost'] * (deviation_vars['cost'][0] + deviation_vars['cost'][1]) +
        weights['water'] * (deviation_vars['water'][0] + deviation_vars['water'][1]),
        GRB.MINIMIZE
    )

    model.addConstr(gp.quicksum(x[suppliers[i]] for i in range(len(suppliers))) == total_demand, "total_demand")
    for i in range(len(suppliers)):
        model.addConstr(x[suppliers[i]] <= supply_capacity[i], f"supply_capacity_{suppliers[i]}")

    model.addConstr(gp.quicksum(cost_per_bag[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['cost'][1] - deviation_vars['cost'][0] == goals['cost'], "cost_goal")
    model.addConstr(gp.quicksum(water_usage[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['water'][1] - deviation_vars['water'][0] == goals['water'], "water_goal")

    model.optimize()

    result = {}
    if model.status == GRB.OPTIMAL:
        selected_suppliers = sorted({suppliers[i]: int(x[suppliers[i]].X) for i in range(len(suppliers)) if x[suppliers[i]].X > 0}.items(), key=lambda item: item[1], reverse=True)
        result['status'] = "Optimal solution found"
        result['purchase'] = selected_suppliers
        result['total_cost'] = round(gp.quicksum(cost_per_bag[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue(), 1)
        result['total_water'] = round(gp.quicksum(water_usage[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue(), 1)
        result['cost_deviation'] = (round(deviation_vars['cost'][0].X, 1), round(deviation_vars['cost'][1].X, 1))
        result['water_deviation'] = (round(deviation_vars['water'][0].X, 1), round(deviation_vars['water'][1].X, 1))
        
        df_selected = df[df['Supplier ID'].isin([s[0] for s in selected_suppliers])].copy()
        df_selected['Cost per bag (euros)'] = df_selected['Cost per bag (euros)'].round(1)
        df_selected['Water usage (liters per bag)'] = df_selected['Water usage (liters per bag)'].round(1)
        df_selected['Farm size (ha)'] = df_selected['Farm size (ha)'].round(1)
        df_selected['Yield (bags per ha)'] = df_selected['Yield (bags per ha)'].round(1)
        result['supplier_data'] = df_selected.to_dict(orient='records')

        # Create Plotly graph
        categories = ['Cost', 'Water Usage']
        goals_values = [goals['cost'], goals['water']]
        achieved_values = [result['total_cost'], result['total_water']]
        deviations_plus = [result['cost_deviation'][0], result['water_deviation'][0]]
        deviations_minus = [result['cost_deviation'][1], result['water_deviation'][1]]

        fig = go.Figure()
        fig.add_trace(go.Bar(x=categories, y=goals_values, name='Goal', marker_color='green'))
        fig.add_trace(go.Bar(x=categories, y=achieved_values, name='Achieved', marker_color='blue'))
        fig.add_trace(go.Bar(x=categories, y=deviations_plus, name='Deviation +', marker_color='red'))
        fig.add_trace(go.Bar(x=categories, y=deviations_minus, name='Deviation -', marker_color='orange'))

        fig.update_layout(title='Goals vs Achieved vs Deviations',
                          xaxis_title='Metrics',
                          yaxis_title='Values',
                          barmode='group')

        # Convert Plotly figure to JSON
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        result['deviation_plot'] = graph_json

    else:
        result['status'] = "No optimal solution found"

    return result

    return result

if __name__ == "__main__":
    app.run(debug=True)