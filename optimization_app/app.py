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
            'wage': float(request.form['weight_wage']),
            'water': float(request.form['weight_water']),
            'quality': float(request.form['weight_quality']),
            'yield': float(request.form['weight_yield']),
        }
        goals = {
            'cost': float(request.form['cost_goal']),
            'wage': float(request.form['wage_goal']),
            'water': float(request.form['water_goal']),
            'quality': float(request.form['quality_goal']),
            'yield': float(request.form['yield_goal']),
        }

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(filepath)
        result = optimize(df, total_demand, weights, goals)
        return render_template('results.html', result=result)
    return render_template('weights.html', filename=filename)

def optimize(df, total_demand, weights, goals):
    suppliers = df['Supplier ID'].tolist()
    supply_capacity = df['Cost per bag (euros)'].tolist()  # Assuming supply capacity is derived from cost per bag
    cost_per_bag = df['Cost per bag (euros)'].tolist()
    wage_per_day = df['Wage per day (euros)'].tolist()
    water_conservation = df['Water conservation (liters per bag)'].tolist()
    quality_of_coffee = df['Quality of coffee (total cup points)'].tolist()
    yield_bags = df['Yield (bags per ha)'].tolist()

    # Create a new model
    model = gp.Model("supplier_selection")

    # Create variables
    x = model.addVars(suppliers, vtype=GRB.INTEGER, name="x", lb=0)
    deviation_vars = {goal: (model.addVar(name=f"d_{goal}_plus", lb=0), model.addVar(name=f"d_{goal}_minus", lb=0)) for goal in goals}

    # Set objective
    model.setObjective(
        gp.quicksum(weights[goal] * (deviation_vars[goal][0] + deviation_vars[goal][1]) for goal in goals),
        GRB.MINIMIZE
    )

    # Add constraints
    model.addConstr(gp.quicksum(x[suppliers[i]] for i in range(len(suppliers))) == total_demand, "total_demand")
    for i in range(len(suppliers)):
        model.addConstr(x[suppliers[i]] <= supply_capacity[i], f"supply_capacity_{suppliers[i]}")

    # Goals with deviation variables
    model.addConstr(gp.quicksum(cost_per_bag[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['cost'][1] - deviation_vars['cost'][0] == goals['cost'], "cost_goal")
    model.addConstr(gp.quicksum(wage_per_day[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['wage'][1] - deviation_vars['wage'][0] == goals['wage'], "wage_goal")
    model.addConstr(gp.quicksum(water_conservation[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['water'][1] - deviation_vars['water'][0] == goals['water'], "water_goal")
    model.addConstr(gp.quicksum(quality_of_coffee[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['quality'][1] - deviation_vars['quality'][0] == goals['quality'], "quality_goal")
    model.addConstr(gp.quicksum(yield_bags[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['yield'][1] - deviation_vars['yield'][0] == goals['yield'], "yield_goal")

    # Optimize model
    model.optimize()

    result = {}
    if model.status == GRB.OPTIMAL:
        result['status'] = "Optimal solution found"
        result['purchase'] = {suppliers[i]: x[suppliers[i]].X for i in range(len(suppliers))}
        result['total_cost'] = gp.quicksum(cost_per_bag[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['total_wage'] = gp.quicksum(wage_per_day[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['total_water'] = gp.quicksum(water_conservation[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['total_quality'] = gp.quicksum(quality_of_coffee[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['total_yield'] = gp.quicksum(yield_bags[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        for goal in goals:
            result[f'{goal}_deviation'] = (deviation_vars[goal][0].X, deviation_vars[goal][1].X)
    else:
        result['status'] = "No optimal solution found"

    return result

if __name__ == "__main__":
    app.run(debug=True)
