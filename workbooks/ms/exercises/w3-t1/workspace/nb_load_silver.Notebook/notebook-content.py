# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
# META       "default_lakehouse_name": "lh_silver",
# META       "default_lakehouse_workspace_id": "2f1c6a0e-8d3b-4c55-9a71-0b6de4f3a210",
# META       "known_lakehouses": [
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

# Silver: clean and conform POS orders landed by the Copy job into Files/pos/.
from pyspark.sql import functions as F

raw = spark.read.json(f"Files/pos/{run_date}/*.json")
clean = (
    raw.dropDuplicates(["order_id", "line_no"])
    .withColumn("order_date", F.to_date("order_ts"))
    .withColumn("net_amount", F.col("qty") * F.col("unit_price") - F.coalesce(F.col("discount"), F.lit(0)))
)
(clean.write.format("delta").mode("overwrite")
    .option("replaceWhere", f"order_date = '{run_date}'")
    .saveAsTable("sales_clean"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
