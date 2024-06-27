'''
App module for the optimization app.
'''

# Download and import required libraries for running the code
# pip install flask
# pip install pandas
# pip install gurobipy
# pip install matplotlib
# pip install plotly
# pip install celery
# pip install redis
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

'''
The first step is to create a Flask application and configure it with a secret key and the upload folder.
This is done in order to store the uploaded files and to keep the session data secure.
'''

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

'''
The second step is to create a Celery instance and configure it with the Flask application.
This is done in order to run the optimization task asynchronously using Celery.
Celery requires a message broker to send and receive messages between the Flask application and the Celery worker.
In this case, we are using Redis as the message broker.
'''

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

'''
The next step is to define the routes for the application.
The index route is used to render the index.html template.
The upload route is used to upload a CSV file containing the supplier data.
The set_weights route is used to set the weights for the cost and water usage, as well as the goals for the cost and water usage.
The optimize route is used to run the optimization task asynchronously using Celery.
The show_scenario route is used to display the results for a specific scenario.
'''

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
    result['scenario'] = scenario  # Pass the scenario to the template
    return render_template('scenario.html', result=result)

'''
The final step is to define the optimize function that will be executed by the Celery worker.
'''

@celery.task
def optimize(df, total_demand, weights, goals, yield_scenario):
    '''
    Function to optimize the supplier selection problem.

    Parameters:
    - df: DataFrame containing the supplier data
    - total_demand: Total demand for coffee bags
    - weights: Dictionary containing the weights for cost and water usage
    - goals: Dictionary containing the goals for cost and water usage
    - yield_scenario: Scenario for the coffee yield (average, high, low)

    Returns:

    A dictionary containing the following
    - status: Status of the optimization (Optimal solution found or No optimal solution found)
    - purchase: List of selected suppliers with the quantity to purchase
    - total_cost: Total cost of purchasing coffee bags
    - total_water: Total water usage for coffee production
    - cost_deviation: Deviation from the cost goal
    - water_deviation: Deviation from the water goal
    - supplier_data: Supplier data for the selected suppliers
    - deviation_plot_cost: Plotly JSON for the cost deviation
    - deviation_plot_water: Plotly JSON for the water deviation
    '''

    suppliers = df['Supplier ID']
    cost_per_bag = df['Cost per bag (euros)']
    water_usage = df['Water usage (liters per bag)']
    farm_size = df['Farm size (ha)']
    yield_per_ha = df['Yield (bags per ha)']

    # Apply yield scenario in case of high or low yield

    if yield_scenario == 'high':
        yield_per_ha = [y * 1.2 for y in yield_per_ha]  # 20% higher than average
    elif yield_scenario == 'low':
        yield_per_ha = [y * 0.8 for y in yield_per_ha]  # 20% lower than average

    # Calculate the supply capacity for each supplier based on the farm size and yield

    supply_capacity = [int(farm_size[i] * yield_per_ha[i]) for i in range(len(suppliers))]

    # Create the optimization model

    model = gp.Model("supplier_selection")

    # Create decision variables

    x = model.addVars(suppliers, vtype=GRB.INTEGER, name="x", lb=0)
    deviation_vars = {
        'cost': (model.addVar(name="d_cost_plus", lb=0), model.addVar(name="d_cost_minus", lb=0)),
        'water': (model.addVar(name="d_water_plus", lb=0), model.addVar(name="d_water_minus", lb=0))
    }

    # Set objective function, which is to minimize the deviation from the goals for cost and water usage
    # given the weights for cost and water usage
    model.setObjective(
        weights['cost'] * (deviation_vars['cost'][0] + deviation_vars['cost'][1]) +
        weights['water'] * (deviation_vars['water'][0] + deviation_vars['water'][1]),
        GRB.MINIMIZE
    )

    # Constraint to ensure that the total demand is met
    model.addConstr(gp.quicksum(x[suppliers[i]] for i in range(len(suppliers))) == total_demand, "total_demand")

    # Constraint to ensure that the supply capacity of each supplier is not exceeded
    for i in range(len(suppliers)):
        model.addConstr(x[suppliers[i]] <= supply_capacity[i], f"supply_capacity_{suppliers[i]}")

    # Constraints to calculate the deviation from the goals for cost and water usage based on the selected suppliers
    model.addConstr(gp.quicksum(cost_per_bag[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['cost'][1] - deviation_vars['cost'][0] == goals['cost'], "cost_goal")
    model.addConstr(gp.quicksum(water_usage[i] * x[suppliers[i]] for i in range(len(suppliers))) + deviation_vars['water'][1] - deviation_vars['water'][0] == goals['water'], "water_goal")

    model.optimize()

    # Extract the results
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

        # Create Plotly graphs
        categories = ['Cost', 'Water Usage']
        goals_values = [goals['cost'], goals['water']]
        achieved_values = [result['total_cost'], result['total_water']]

        # Plot for Cost
        fig_cost = go.Figure()
        fig_cost.add_trace(go.Bar(x=['Cost'], y=[goals['cost']], name='Goal', marker_color='green'))
        fig_cost.add_trace(go.Bar(x=['Cost'], y=[result['total_cost']], name='Achieved', marker_color='blue'))
        fig_cost.add_trace(go.Scatter(x=['Cost', 'Cost'], y=[goals['cost'], result['total_cost']], mode='lines', name='Deviation', line=dict(color='red', dash='dash')))
        fig_cost.update_layout(title='Cost: Goal vs Achieved',
                               xaxis_title='Metrics',
                               yaxis_title='Values',
                               barmode='group')

        # Plot for Water Usage
        fig_water = go.Figure()
        fig_water.add_trace(go.Bar(x=['Water Usage'], y=[goals['water']], name='Goal', marker_color='green'))
        fig_water.add_trace(go.Bar(x=['Water Usage'], y=[result['total_water']], name='Achieved', marker_color='blue'))
        fig_water.add_trace(go.Scatter(x=['Water Usage', 'Water Usage'], y=[goals['water'], result['total_water']], mode='lines', name='Deviation', line=dict(color='red', dash='dash')))
        fig_water.update_layout(title='Water Usage: Goal vs Achieved',
                                xaxis_title='Metrics',
                                yaxis_title='Values',
                                barmode='group')

        # Convert Plotly figures to JSON
        graph_cost_json = json.dumps(fig_cost, cls=plotly.utils.PlotlyJSONEncoder)
        graph_water_json = json.dumps(fig_water, cls=plotly.utils.PlotlyJSONEncoder)
        result['deviation_plot_cost'] = graph_cost_json
        result['deviation_plot_water'] = graph_water_json

    else:
        result['status'] = "No optimal solution found"

    return result

if __name__ == "__main__":
    app.run(debug=True)