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
        weight_cost = float(request.form['weight_cost'])
        weight_carbon = float(request.form['weight_carbon'])
        weight_quality = float(request.form.get('weight_quality', 0))
        weight_wage = float(request.form.get('weight_wage', 0))
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(filepath)
        result = optimize(df, weight_cost, weight_carbon, weight_quality, weight_wage)
        return render_template('results.html', result=result)
    return render_template('weights.html', filename=filename)

def optimize(df, weight_cost, weight_carbon, weight_quality, weight_wage):
    suppliers = df['Supplier'].tolist()
    supply_capacity = df['Supply Capacity'].tolist()
    cost_per_kg = df['Cost per kg'].tolist()
    carbon_footprint_per_kg = df['Carbon Footprint per kg'].tolist()
    quality_score = df.get('Quality Score', [0] * len(suppliers)).tolist()
    wage_per_kg = df.get('Wage per kg', [0] * len(suppliers)).tolist()
    total_demand = 1000  # This can also be parameterized if needed

    cost_goal = 10000
    carbon_goal = 2000
    quality_goal = 85
    wage_goal = 5

    # Create a new model
    model = gp.Model("supplier_selection")

    # Create variables
    x = model.addVars(suppliers, vtype=GRB.INTEGER, name="x", lb=0)
    d1_plus = model.addVar(name="d1_plus", lb=0)
    d1_minus = model.addVar(name="d1_minus", lb=0)
    d2_plus = model.addVar(name="d2_plus", lb=0)
    d2_minus = model.addVar(name="d2_minus", lb=0)
    d3_plus = model.addVar(name="d3_plus", lb=0)
    d3_minus = model.addVar(name="d3_minus", lb=0)
    d4_plus = model.addVar(name="d4_plus", lb=0)
    d4_minus = model.addVar(name="d4_minus", lb=0)

    # Set objective
    model.setObjective(weight_cost * (d1_plus + d1_minus) + 
                       weight_carbon * (d2_plus + d2_minus) + 
                       weight_quality * (d3_plus + d3_minus) +
                       weight_wage * (d4_plus + d4_minus), GRB.MINIMIZE)

    # Add constraints
    model.addConstr(gp.quicksum(x[suppliers[i]] for i in range(len(suppliers))) == total_demand, "total_demand")
    for i in range(len(suppliers)):
        model.addConstr(x[suppliers[i]] <= supply_capacity[i], f"supply_capacity_{suppliers[i]}")

    # Goals with deviation variables
    model.addConstr(gp.quicksum(cost_per_kg[i] * x[suppliers[i]] for i in range(len(suppliers))) + d1_minus - d1_plus == cost_goal, "cost_goal")
    model.addConstr(gp.quicksum(carbon_footprint_per_kg[i] * x[suppliers[i]] for i in range(len(suppliers))) + d2_minus - d2_plus == carbon_goal, "carbon_goal")
    model.addConstr(gp.quicksum(quality_score[i] * x[suppliers[i]] for i in range(len(suppliers))) + d3_minus - d3_plus == quality_goal, "quality_goal")
    model.addConstr(gp.quicksum(wage_per_kg[i] * x[suppliers[i]] for i in range(len(suppliers))) + d4_minus - d4_plus == wage_goal, "wage_goal")

    # Optimize model
    model.optimize()

    result = {}
    if model.status == GRB.OPTIMAL:
        result['status'] = "Optimal solution found"
        result['purchase'] = {suppliers[i]: x[suppliers[i]].X for i in range(len(suppliers))}
        result['total_cost'] = gp.quicksum(cost_per_kg[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['total_carbon'] = gp.quicksum(carbon_footprint_per_kg[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['total_quality'] = gp.quicksum(quality_score[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['total_wage'] = gp.quicksum(wage_per_kg[i] * x[suppliers[i]].X for i in range(len(suppliers))).getValue()
        result['cost_deviation'] = (d1_plus.X, d1_minus.X)
        result['carbon_deviation'] = (d2_plus.X, d2_minus.X)
        result['quality_deviation'] = (d3_plus.X, d3_minus.X)
        result['wage_deviation'] = (d4_plus.X, d4_minus.X)
    else:
        result['status'] = "No optimal solution found"

    return result

if __name__ == "__main__":
    app.run(debug=True)
