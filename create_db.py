import duckdb
import os

# Delete existing database if it exists
if os.path.exists('maria_ap7.duckdb'):
    print("Removing existing database...")
    os.remove('maria_ap7.duckdb')

# Create a new database connection
con = duckdb.connect('maria_ap7.duckdb')

try:
    # Import the CSV files into DuckDB tables
    print("Importing geo_cal_vel data...")
    con.execute("""
        CREATE TABLE geo_cal_vel AS 
        SELECT * FROM read_csv_auto('preMARIA_v2_geo-cal-vel-int-ret_v1_vel_int_cal_mob_1h_new_etds_5.csv')
    """)

    print("Importing predictions data...")
    con.execute("""
        CREATE TABLE predictions AS 
        SELECT 
            "Any" as Anyo,  -- Rename Any to Anyo
            mes,
            dia,
            hor,
            via,
            pk,
            mean_speed_pred,
            percentile_10_pred,
            intTot_pred,
            intP_pred
        FROM read_csv_auto('predictions_model_LSTMModel_granularity_1h_projection_1hour_iter13_YES_geo_YES_vw.csv')
    """)

    # Verify the imports
    print("\nVerifying imports:")
    print("\ngeo_cal_vel table:")
    print(con.execute("SELECT COUNT(*) FROM geo_cal_vel").fetchone()[0], "rows")
    print("\nSchema:")
    print(con.execute("DESCRIBE geo_cal_vel").fetchall())

    print("\npredictions table:")
    print(con.execute("SELECT COUNT(*) FROM predictions").fetchone()[0], "rows")
    print("\nSchema:")
    print(con.execute("DESCRIBE predictions").fetchall())

    print("\nDatabase creation completed successfully!")

except Exception as e:
    print(f"\nError occurred: {str(e)}")
    # If there's an error, try to clean up
    if os.path.exists('maria_ap7.duckdb'):
        os.remove('maria_ap7.duckdb')
    raise

finally:
    # Close the connection
    con.close() 