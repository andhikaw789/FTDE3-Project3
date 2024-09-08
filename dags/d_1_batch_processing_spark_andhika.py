from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import psycopg2
import os
from sqlalchemy import create_engine
import pandas as pd


from datetime import datetime



def fun_top_countries_get_data(**kwargs):
    spark = SparkSession.builder\
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.0")\
        .master("local").appName("Pyspark_Postgres")\
        .getOrCreate()

    df_country = spark.read.format("jdbc")\
    .option("url", "jdbc:postgresql://34.42.78.12:5434/postgres")\
    .option("dbtable", "country")\
    .option("user", "airflow")\
    .option("password", "airflow")\
    .option("driver", "org.postgresql.Driver")\
    .load()
    df_country.createOrReplaceTempView("df_country")

    df_city = spark.read.format("jdbc")\
    .option("url", "jdbc:postgresql://34.42.78.12:5434/postgres")\
    .option("dbtable", "city")\
    .option("user", "airflow")\
    .option("password", "airflow")\
    .option("driver", "org.postgresql.Driver")\
    .load()
    df_city.createOrReplaceTempView("df_city")

    df_result = spark.sql("""
        SELECT
            country,
            COUNT(country) as total,
            current_date() as date
        FROM df_country AS co
        INNER JOIN df_city AS ci
        ON ci.country_id = co.country_id
        GROUP BY country""")
    df_result.createOrReplaceTempView("df_result")

    
    df_result.write.mode("append")\
        .partitionBy("date")\
        .option("compression", "snappy")\
        .save("data_result_task_1")
    

def fun_top_countries_load_data(**kwargs):
    df = pd.read_parquet('data_result_task_1')
    engine = create_engine('mysql+mysqlconnector://4FFFhK9fXu6JayE.root:9v07S0pKe4ZYCkjE@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test', echo=False)
    df.to_sql(name='top_country_andhika', con=engine)

def fun_total_film_get_data(**kwargs):
    spark = SparkSession.builder\
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.0")\
        .master("local").appName("Pyspark_Postgres")\
        .getOrCreate()
    
    df_film = spark.read.format("jdbc")\
    .option("url", "jdbc:postgresql://34.42.78.12:5434/postgres")\
    .option("dbtable", "film")\
    .option("user", "airflow")\
    .option("password", "airflow")\
    .option("driver", "org.postgresql.Driver")\
    .load()
    df_film.createOrReplaceTempView("df_film")

    df_film_cat = spark.read.format("jdbc")\
    .option("url", "jdbc:postgresql://34.42.78.12:5434/postgres")\
    .option("dbtable", "film_category")\
    .option("user", "airflow")\
    .option("password", "airflow")\
    .option("driver", "org.postgresql.Driver")\
    .load()
    df_film_cat.createOrReplaceTempView("df_film_cat")

    df_category = spark.read.format("jdbc")\
    .option("url", "jdbc:postgresql://34.42.78.12:5434/postgres")\
    .option("dbtable", "category")\
    .option("user", "airflow")\
    .option("password", "airflow")\
    .option("driver", "org.postgresql.Driver")\
    .load()
    df_category.createOrReplaceTempView("df_category")

    df_result_2 = spark.sql("""
              select y.category_id,
                z.name as category_name,
                count(z.name) as total_film,
                current_date() as date
              from df_film as x
              inner join df_film_cat as y
              on x.film_id = y.film_id
              inner join df_category as z
              on y.category_id = z.category_id
              group by y.category_id, z.name
              """)\
              .sort("total_film", ascending=False)
    df_result_2.createOrReplaceTempView("df_result_2")

    df_result_2.write.mode("append")\
        .partitionBy("date")\
        .option("compression", "snappy")\
        .save("data_result_task_2")


def fun_total_film_load_data(**kwargs):
    df_2 = pd.read_parquet('data_result_task_2')
    engine = create_engine('mysql+mysqlconnector://4FFFhK9fXu6JayE.root:9v07S0pKe4ZYCkjE@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test', echo=False)
    df_2.to_sql(name='total_film_andhika', con=engine)

with DAG(
    dag_id = 'd_1_batch_processing_spark_andhika',
    start_date = datetime(2022, 5, 28),
    schedule_interval = '00 23 * * *',
    catchup = False
    ) as dag:

    start_task = EmptyOperator(
        task_id = 'start'
    )

    op_top_countries_get_data = PythonOperator(
        task_id = 'top_countries_get_data',
        python_callable = fun_top_countries_get_data
    )

    op_top_countries_load_data = PythonOperator(
        task_id = 'top_countries_load_data',
        python_callable = fun_top_countries_load_data
    )

    op_total_film_get_data = PythonOperator(
        task_id = 'total_film_get_data',
        python_callable = fun_total_film_get_data
    )

    op_total_film_load_data = PythonOperator(
        task_id = 'total_film_load_data',
        python_callable = fun_total_film_load_data
    )


    end_task = EmptyOperator(
        task_id = 'end'
    )

    start_task >> op_top_countries_get_data >> op_top_countries_load_data >> end_task
    start_task >> op_total_film_get_data >> op_total_film_load_data >> end_task

