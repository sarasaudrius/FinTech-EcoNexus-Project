# Data Generation Process

The data used in EcoNexus is synthetic but is grounded in real-world numbers from reports and studies in the coffee industry. 
This ensures that the generated data is realistic and provides meaningful insights while being fictitious.

Data of 30 suppliers were generated to minimize computational complexity and ensure that the algorithm can smoothly process the workflow.

## Variables generated and the assumptions made when generating variables:
- `Farm Size (ha)`: This variable denotes the farm size measured in hectares. [According to some studies, 80-95% percent of all farms are smaller than 5 ha, therefore, the values generated were primarily between 0 and 5 ha](https://www.sciencedirect.com/science/article/pii/S1877343524000198#bib3)
- `Cost per bag (euros)`: This variable denotes the cost per 60kg bag of coffee, with a mean of 150 euros and a standard deviation of 10% of the mean.
  [According to a report by Global Coffee Platform, the average coffee price in Brazil (the largest coffee exporter in the world), it is ~150 per bag (1 bag = 60 kg of coffee beans)](https://www.globalcoffeeplatform.org/latest/2023/first-findings-on-living-income-in-brazilian-coffee-production/)
- `Wage per day (euros)`: [The daily wage paid to workers, with a mean of 9 euros and a standard deviation of 10% of the mean](https://www.scienceopen.com/hosted-document?doi=10.13169/jfairtrade.4.2.0002) 
- `Water usage (liters per bag)`: [The amount of water used per 60kg bag of coffee, with a mean of 3600 liters and a standard deviation of 10% of the mean](https://www.sciencedirect.com/science/article/pii/S0921344922000234). This variable is clipped to ensure reasonable values.
- `Quality of coffee (total cup points)`: The quality score of the coffee, measured out of 100 points, with a mean of 80 and a standard deviation of 5% of the mean. This variable is clipped to ensure it remains between 0 and 100.
- `Yield (bags per ha)`: [The yield of coffee, measured in 60kg bags per hectare, with a mean of 43 and a standard deviation of 10% of the mean](https://www.globalcoffeeplatform.org/latest/2023/first-findings-on-living-income-in-brazilian-coffee-production/)
