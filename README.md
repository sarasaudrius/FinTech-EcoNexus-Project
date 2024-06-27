![EcoNexusLogo-removebg-preview](https://github.com/sarasaudrius/FinTech-EcoNexus-Project/assets/149503993/af9fa12a-6572-45a0-ad32-2b190b22fd7d)

# EcoNexus: Integrating Financial and ESG Goals with Multi-Objective Optimization

## Overview

EcoNexus is a Software as a Service (SaaS) platform designed to integrate financial performance and Environmental, Social, and Governance (ESG) goals. By utilizing multi-objective optimization algorithms, EcoNexus provides businesses with prescriptive solutions that consider both financial metrics and sustainability objectives, enabling informed decision-making.

## Target Industry

The initial focus of EcoNexus is the coffee industry, where sustainable sourcing and adherence to ESG practices in the supply chain are paramount. Companies like Starbucks, Nespresso, and JDE benefit from ensuring their suppliers meet fair labor practices, minimize water usage, and reduce environmental impacts.

## Key Features

1. **Multi-Objective Optimization**: Uses weighted goal programming to balance financial goals (e.g., cost minimization, profit maximization) with ESG objectives based on company preferences.
2. **Scenario Analysis**: Offers dynamic scenario analysis to handle uncertainties in supplier information, helping organizations adapt their business and financial planning.

## Technologies

- **Python**: Core algorithm development.
- **Flask**: Web development framework.
- **Gurobi Optimizer**: Solver for complex mathematical optimization problems, including linear programming and mixed-integer programming.

## Goals

EcoNexus aims to equip coffee businesses with a tool that integrates financial performance metrics with ESG goals. Through optimization algorithms and scenario analysis, it guides coffee companies in making balanced decisions that support both financial growth and sustainability.

## Problem Description: Supplier Selection with Multi-Objective Optimization

Coffee companies face the challenge of optimizing their supply chain and selecting suppliers that align with their sustainability goals. EcoNexus helps in this by considering multiple objectives:

- **Financial Goal**: Minimize total cost.
- **ESG Goals**: Minimize water usage.

### Constraints

- **Demand Constraint**: Total quantity sourced must meet the company's demand.
- **Supply Capacity Constraints**: Quantity from each supplier should not exceed their maximum capacity.
- **Additional Constraints**: Optional constraints like region-specific sourcing, transportation distance, etc.

### Input Data

The system accepts the following inputs:

- Supplier attributes (supply capacity, cost per unit, water usage per unit).
- Total demand.
- Goal values and weights for each objective.
- Additional constraints or requirements.

## How to Run the Application

To run the EcoNexus application, follow these steps:

1. **Install Required Libraries**:
   ```bash
   pip install flask pandas gurobipy matplotlib plotly celery redis
2. **Run the Flask Application**:
    Open the folder in Visual Studio Code.
    Run the app.py script. In the output, a link will be provided.
    Open the provided link with Ctrl+Click to access the web application.

## Application Workflow
1. Upload Supplier Data: Navigate to the upload page and upload a CSV file with supplier data.
2. Set Weights and Goals: Enter the weights for cost and water usage, as well as the goals for these metrics.
3. View Results: Analyze the optimization results, including selected suppliers, total cost, total water usage, and deviations from goals.
