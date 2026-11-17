# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "6e0d8f4a-1b2c-4d3e-8f90-a1b2c3d4e5f6",
# META       "default_lakehouse_name": "lh_gold",
# META       "default_lakehouse_workspace_id": "2f1c6a0e-8d3b-4c55-9a71-0b6de4f3a210",
# META       "known_lakehouses": [
# META         {
# META           "id": "6e0d8f4a-1b2c-4d3e-8f90-a1b2c3d4e5f6"
# META         },
# META         {
# META           "id": "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
# META         }
# META       ]
# META     }
# META   }
# META }

# PARAMETERS CELL ********************

# Parameters
run_date = "2026-10-06"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Gold: daily sales by store and category for the Contoso Retail sales semantic model.
# Reads silver from the attached lakehouse lh_silver and writes to the DEFAULT lakehouse (lh_gold).
from pyspark.sql import functions as F

silver = spark.read.table("lh_silver.sales_clean").where(F.col("order_date") == F.lit(run_date))
daily = (
    silver.groupBy("order_date", "store_id", "category")
    .agg(F.sum("net_amount").alias("net_sales"), F.countDistinct("order_id").alias("orders"))
)
(daily.write.format("delta").mode("overwrite")
    .option("replaceWhere", f"order_date = '{run_date}'")
    .saveAsTable("sales_daily"))
print(f"gold.sales_daily rows written for {run_date}: {daily.count()}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
