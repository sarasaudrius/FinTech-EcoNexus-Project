'''
App module for the optimization app.
'''

### Import necessary libraries
from flask import Flask, request, render_template, redirect, url_for, flash
import os
import pandas as pd
import gurobipy as gp
from gurobipy import GRB

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Route for uploading files
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

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(filepath)
        result = optimize(df, total_demand, weights, goals)
        return render_template('results.html', result=result)
    return render_template('weights.html', filename=filename)

def optimize(df, total_demand, weights, goals):
    suppliers = df['Supplier ID'].tolist()
    cost_per_bag = df['Cost per bag (euros)'].tolist()
    water_usage = df['Water usage (liters per bag)'].tolist()
    farm_size = df['Farm size (ha)'].tolist()
    yield_per_ha = df['Yield (bags per ha)'].tolist()
    
    supply_capacity = [farm_size[i] * yield_per_ha[i] for i in range(len(suppliers))]

    # Create a new model
    model = gp.Model("supplier_selection")

    # Create variables
    x = model.addVars(suppliers, vtype=GRB.INTEGER, name="x", lb=0)
    deviation_vars = {
        'cost': (model.addVar(name="d_cost_plus", lb=0), model.addVar(name="d_cost_minus", lb=0)),
        'water': (model.addVar(name="d_water_plus", lb=0), model.addVar(name="d_water_minus", lb=0))
    }

    # Set objective
    model.setObjective(
        weights['cost'] * (deviation_vars['cost'][0] + deviation_vars['cost'][1]) +
        weights['water'] * (deviation_vars['water'][0] + deviation_vars['water'][1]),
        GRB.MINIMIZE
    )

    # Add constraints
    model.addConstr(gp.quicksum(x[suppliers[i]] for i in range(len(suppliers))) == total_demand, "total_demand")
    for i in range(len(suppliers)):
        model.addConstr(x[suppliers[i]] <= supply_capacity[i], f"supply_capacity_{suppliers[i]}")

    # Goals with deviation variables
    model.addConstr(gp.quicksum(cost_per_bag[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['cost'][1] - deviation_vars['cost'][0] == goals['cost'], "cost_goal")
    model.addConstr(gp.quicksum(water_usage[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['water'][1] - deviation_vars['water'][0] == goals['water'], "water_goal")

    # Optimize model
    model.optimize()

    result = {}
    if model.status == GRB.OPTIMAL:
        result['status'] = "Optimal solution found"
        result['purchase'] = {suppliers[i]: x[suppliers[i]].X for i in range(len(suppliers))}
        result['total_cost'] = gp.quicksum(cost_per_bag[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['total_water'] = gp.quicksum(water_usage[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['cost_deviation'] = (deviation_vars['cost'][0].X, deviation_vars['cost'][1].X)
        result['water_deviation'] = (deviation_vars['water'][0].X, deviation_vars['water'][1].X)
    else:
        result['status'] = "No optimal solution found"

    return result

if __name__ == "__main__":
    app.run(debug=True)
