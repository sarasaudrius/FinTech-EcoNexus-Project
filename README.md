Sure, here's a concise README file that describes the EcoNexus innovation and its objectives:

# EcoNexus: Integrating Financial and ESG Goals with Multi-Objective Optimization

## Overview

EcoNexus is a Software as a Service (SaaS) platform developed by Bloomberg Professional Services that aims to bridge the gap between financial performance and Environmental, Social, and Governance (ESG) goals for businesses. It leverages multi-objective optimization algorithms to simultaneously consider a company's financial metrics and sustainability objectives, providing prescriptive solutions for informed decision-making.

![image](https://github.com/sarasaudrius/FinTech-EcoNexus-Project/assets/149503993/537803c9-3af4-47a9-9cba-8e23141b7191)


## Target Industry

The initial target industry for EcoNexus is the coffee industry, where sustainable sourcing and adhering to ESG practices within the supply chain are critical. Companies like Starbucks, Nespresso, and JDE need to ensure their suppliers meet fair labor practices, minimize water usage, and reduce environmental impact.

## Key Features

1. **Multi-Objective Optimization**: EcoNexus employs weighted goal programming, a multi-objective optimization technique, to assign different weights to financial goals (e.g., cost minimization, profit maximization) and ESG objectives based on the company's preferences. This allows for the simultaneous optimization of multiple objectives according to their assigned weights.

2. **Scenario Analysis**: Recognizing the potential uncertainty in supplier information and measures, EcoNexus provides scenario analysis capabilities. This feature dynamically generates recommendations based on different scenarios, enabling organizations to adjust their business and financial planning accordingly.

## Technologies

1. **Python**. The algorithm is created with Python.
2. **Flask**. Web development is done with Flask.
3. **Gurobi Optimizer**: A state-of-the-art solver for complex mathematical optimization problems, including linear programming and mixed-integer programming. Gurobi is chosen for its flexibility, speed, efficiency, and scalability.

## Goals

The primary objective of EcoNexus is to provide coffee businesses with a powerful tool that integrates financial performance metrics with ESG goals. By utilizing optimization algorithms and scenario analysis, EcoNexus aims to guide coffee companies in making informed decisions that align with both their financial and sustainability objectives, ultimately enabling them to achieve a balanced approach to growth and environmental responsibility.

## Problem Description: Supplier Selection with Multi-Objective Optimization

One of the primary problems that coffee companies currently face is optimizing their supply chain network and selecting suppliers that align with their sustainability goals. Sustainable sourcing of coffee is a multifaceted problem that encompasses all three areas of ESG. Specifically, this tool would help coffee companies select their suppliers and the amount of coffee that is necessary to order from them to fulfill their demand. The system is flexible, allowing the company to input its own goals, constraints, and relevant data.

The system considers the following objectives, which can be assigned different weights based on the company's priorities:

Financial Goal: Minimize the total cost or keep it within a specified budget.
ESG Goals: Minimize the total carbon footprint or keep it below a specified threshold.
Quality Goal: Achieve a minimum specified quality score based on the weighted average of the selected suppliers.
Social Goal: Ensure fair wages are paid to coffee farmers by the selected suppliers, above a specified minimum wage per unit.

Constraints:
The system should incorporate the following constraints:

Demand Constraint: The total quantity sourced from the selected suppliers should meet the company's demand.
Supply Capacity Constraints: The quantity sourced from each supplier should not exceed their maximum supply capacity.
Additional Constraints: The company can specify additional constraints based on their requirements, such as maximum or minimum sourcing from specific regions, maximum transportation distance, or any other relevant factors.

Input Data:
The system should be designed to accept the following input data from the company:

List of potential suppliers with their respective attributes, such as:

Supply capacity
Cost per unit
Carbon footprint per unit
Quality score of the coffee products
Wage paid to coffee farmers per unit


Total demand
Goal values and weights for each objective (e.g., maximum budget, carbon footprint threshold, minimum quality score, minimum wage per unit)
Any additional constraints or requirements
