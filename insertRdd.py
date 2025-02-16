import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, collect_list, struct, broadcast, sort_array, split,
    to_json, from_json, expr, explode,trim
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, BooleanType, DoubleType
)



#### ---- Schema

# Define schemas for each dataset
title_basics_schema = StructType([
    StructField("tconst", StringType(), nullable=False),
    StructField("titleType", StringType(), nullable=True),
    StructField("primaryTitle", StringType(), nullable=True),
    StructField("originalTitle", StringType(), nullable=True),
    StructField("isAdult", IntegerType(), nullable=True),
    StructField("startYear", IntegerType(), nullable=True),
    StructField("endYear", IntegerType(), nullable=True),
    StructField("runtimeMinutes", IntegerType(), nullable=True),
    StructField("genres", StringType(), nullable=True),
])

name_basics_schema = StructType([
    StructField("nconst", StringType(), nullable=False),
    StructField("primaryName", StringType(), nullable=True),
    StructField("birthYear", IntegerType(), nullable=True),
    StructField("deathYear", IntegerType(), nullable=True),
    StructField("primaryProfession", StringType(), nullable=True),
    StructField("knownForTitles", StringType(), nullable=True),
])

title_episode_schema = StructType([
    StructField("tconst", StringType(), nullable=False),
    StructField("parentTconst", StringType(), nullable=True),
    StructField("seasonNumber", IntegerType(), nullable=True),
    StructField("episodeNumber", IntegerType(), nullable=True),
])

title_principals_schema = StructType([
    StructField("tconst", StringType(), nullable=False),
    StructField("ordering", IntegerType(), nullable=True),
    StructField("nconst", StringType(), nullable=True),
    StructField("category", StringType(), nullable=True),
    StructField("job", StringType(), nullable=True),
    StructField("characters", StringType(), nullable=True),
])

title_ratings_schema = StructType([
    StructField("tconst", StringType(), nullable=False),
    StructField("averageRating", DoubleType(), nullable=True),
    StructField("numVotes", IntegerType(), nullable=True),
])

##### --- SESSION + DATA READING

def create_spark_session():
    """
    Create and return a Spark session configured for MongoDB.

    Returns:
        SparkSession: A configured SparkSession object.
    """
    
    return SparkSession.builder \
        .appName("IMDbProcessing") \
        .master("local[*]") \
        .config("spark.driver.memory", "10g") \
        .config("spark.executor.memory", "10g") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.1") \
        .config("spark.mongodb.write.connection.uri", "mongodb://localhost:27017/imdbSpark") \
        .getOrCreate()


def read_datasets(spark):
    """
    Load the IMDb TSV datasets into DataFrames with explicit schemas.

    Args:
        spark (SparkSession): The active Spark session.

    Returns:
        tuple: A tuple containing the following DataFrames:
            - title_basics (DataFrame): Title metadata.
            - name_basics (DataFrame): People metadata.
            - title_episode (DataFrame): Episode metadata.
            - title_principals (DataFrame): Cast and crew metadata.
            - title_ratings (DataFrame): Ratings metadata.
    """
    
    logging.info("Reading datasets ...")
    
    title_basics = spark.read.csv(
        "Datasets/title.basics.tsv", sep="\t", header=True, schema=title_basics_schema, nullValue="\\N"
    )
    name_basics = spark.read.csv(
        "Datasets/name.basics.tsv", sep="\t", header=True, schema=name_basics_schema, nullValue="\\N"
    )
    title_episode = spark.read.csv(
        "Datasets/title.episode.tsv", sep="\t", header=True, schema=title_episode_schema, nullValue="\\N"
    )
    title_principals = spark.read.csv(
        "Datasets/title.principals.tsv", sep="\t", header=True, schema=title_principals_schema, nullValue="\\N"
    )
    title_ratings = spark.read.csv(
        "Datasets/title.ratings.tsv", sep="\t", header=True, schema=title_ratings_schema, nullValue="\\N"
    )

    title_basics.cache()
    return title_basics, name_basics, title_episode, title_principals, title_ratings

###### ---- DATA PROCESSING

def process_principals(title_principals, name_basics):
    """
    Process title principals data by joining it with name_basics to enrich
    with people's details and aggregating them per title.

    Args:
        title_principals (DataFrame): DataFrame containing title principals.
        name_basics (DataFrame): DataFrame containing people's information.

    Returns:
        DataFrame: A DataFrame with aggregated principal details per title.
    """
    
    logging.info("Processing principals and joining with people data ...")
    principals_people = title_principals.join(
        broadcast(name_basics), on="nconst", how="left"
    ).select(
        "tconst", "ordering", "nconst",
        col("primaryName").alias("name"),
        "category", "job", "characters",
        "birthYear", "deathYear", "primaryProfession"
    )
    
    # Debug: inspect the joined DataFrame
    logging.info("Schema of principals_people:")
    principals_people.printSchema()
    #principals_people.show(5, truncate=False)
    
    aggregated_principals = principals_people.groupBy("tconst") \
        .agg(sort_array(collect_list(
            struct("ordering", "name", "category", "job", "characters",
                   "nconst", "birthYear", "deathYear", "primaryProfession")
        ), asc=True).alias("people"))
    
    # Debug: inspect the aggregated DataFrame
    logging.info("Schema of aggregated_principals:")
    aggregated_principals.printSchema()
    #aggregated_principals.show(5, truncate=False)
    
    return aggregated_principals


def prepare_title_collections(title_basics, aggregated_principals, title_ratings):
    """
    Prepare collections for Movies, TV Series, and Shorts by:
      - Filtering by title type.
      - Renaming columns to match the target schema.
      - Joining aggregated principals and ratings.

    Args:
        title_basics (DataFrame): DataFrame containing basic title details.
        aggregated_principals (DataFrame): DataFrame with aggregated principal data.
        title_ratings (DataFrame): DataFrame containing title ratings.

    Returns:
        tuple: A tuple containing:
            - movies_total (DataFrame): Processed movies collection.
            - tv_series_total (DataFrame): Processed TV series collection.
            - shorts_total (DataFrame): Processed shorts collection.
    """
    logging.info("Preparing title collections ...")
    
    # Movies: they only have start year
    movies_basic = title_basics.filter(col("titleType") == "movie") \
        .withColumnRenamed("startYear", "year") \
        .withColumnRenamed("primaryTitle", "title") \
        .drop("titleType")\
        .drop("endYear")
    
    # TV Series
    tv_series_basic = title_basics.filter(col("titleType") == "tvSeries") \
        .withColumnRenamed("primaryTitle", "title") \
        .drop("titleType")
    
    # Shorts: they only have start year
    shorts_basic = title_basics.filter(col("titleType") == "short") \
        .withColumnRenamed("startYear", "year") \
        .withColumnRenamed("primaryTitle", "title") \
        .drop("titleType")\
        .drop("endYear")
    
    # Convert genres string to array for each title type
    movies_basic = movies_basic.withColumn("genres", split(col("genres"), ","))
    tv_series_basic = tv_series_basic.withColumn("genres", split(col("genres"), ","))
    shorts_basic = shorts_basic.withColumn("genres", split(col("genres"), ","))
    
    # Join in aggregated principals (people) for each title.
    movies_with_people = movies_basic.join(aggregated_principals, on="tconst", how="left")
    tv_series_with_people = tv_series_basic.join(aggregated_principals, on="tconst", how="left")
    shorts_with_people = shorts_basic.join(aggregated_principals, on="tconst", how="left")
    
    # Join ratings and embed them as a nested struct.
    movies_total = movies_with_people.join(title_ratings, on="tconst", how="left") \
        .withColumn("rating", struct(col("numVotes"), col("averageRating"))) \
        .drop("numVotes", "averageRating")
    
    tv_series_total = tv_series_with_people.join(title_ratings, on="tconst", how="left") \
        .withColumn("rating", struct(col("numVotes"), col("averageRating"))) \
        .drop("numVotes", "averageRating")
    
    shorts_total = shorts_with_people.join(title_ratings, on="tconst", how="left") \
        .withColumn("rating", struct(col("numVotes"), col("averageRating"))) \
        .drop("numVotes", "averageRating")
    
    return movies_total, tv_series_total, shorts_total


def add_episodes_to_tv_series(tv_series_total, title_episode, title_basics, title_ratings):
    """
    Enrich the TV series collection by adding episode details.

    Steps:
      - Join title_episode with title_basics to fetch episode metadata.
      - Create an ordering structure for episodes (Season, Episode).
      - Group episodes by the parent TV series.

    Args:
        tv_series_total (DataFrame): DataFrame of processed TV series.
        title_episode (DataFrame): DataFrame of episode information.
        title_basics (DataFrame): DataFrame with title metadata.
        title_basics (DataFrame): DataFrame with rating metadata.

    Returns:
        DataFrame: Updated TV series DataFrame with embedded episodes.
    """
    logging.info("Adding episode details to TV Series ...")
    
    episodes_details = title_episode.join(
        title_basics.select(
            col("tconst").alias("ep_tconst"),
            col("primaryTitle").alias("ep_title"),
            col("isAdult").alias("ep_isAdult"),
            col("startYear").alias("ep_year"),
            col("runtimeMinutes").alias("ep_runtime"),
            "genres"  # include if needed
        ),
        title_episode.tconst == col("ep_tconst"),
        how="left"
    )
    
    # Build ordering for episodes
    episodes_details = episodes_details.withColumn("ordering", 
        struct(col("seasonNumber").alias("Season"), col("episodeNumber").alias("Episode"))
    )
    
    episodes_with_rating = episodes_details.join(title_ratings, on="tconst", how="left") \
        .withColumn("rating", struct(col("numVotes"), col("averageRating"))) \
        .drop("numVotes", "averageRating")
    
    episodes_final = episodes_with_rating.select(
        "parentTconst",
        col("ep_title").alias("Title"),
        col("ep_isAdult").alias("isAdult"),
        col("ep_year").alias("year"),
        col("ep_runtime").alias("runtime"),
        "ordering",
        "rating"
    )
    
    # Group episodes by the parent TV series and optionally sort them
    episodes_agg = episodes_final.groupBy("parentTconst") \
        .agg(sort_array(collect_list(
            struct("Title", "isAdult", "year", "runtime", "ordering", "rating")
        )).alias("episodes"))
    
    tv_series_total = tv_series_total.join(
        episodes_agg,
        tv_series_total.tconst == episodes_agg.parentTconst,
        how="left"
    ).drop("parentTconst")
    
    return tv_series_total

def process_people(name_basics, title_basics):
    """
    Process the people collection by:
      - Splitting primaryProfession and knownForTitles into arrays.
      - Enriching knownForTitles with metadata from title_basics.
      - Aggregating knownForTitles into a structured list.

    Args:
        name_basics (DataFrame): DataFrame containing people metadata.
        title_basics (DataFrame): DataFrame containing title metadata.

    Returns:
        DataFrame: Processed people DataFrame with enriched mainTitles.
    """
    logging.info("Processing people and enriching with main titles ...")
    
    # Convert primaryProfession and knownForTitles to arrays
    people_df = name_basics \
        .withColumn("primaryProfession", split(col("primaryProfession"), ",")) \
        .withColumn("knownForTitlesArray", split(col("knownForTitles"), ","))
    
    # Explode knownForTitles to get one row per title
    exploded = people_df.withColumn("explodedTconst", explode("knownForTitlesArray"))
    exploded = exploded.withColumn("explodedTconst", trim(col("explodedTconst")))
    
    # Prepare a lookup DataFrame from title.basics with tconst, primaryTitle, and startYear
    titles_lookup = title_basics.select(
        col("tconst"),
        col("primaryTitle").alias("title"),
        col("startYear").alias("year")
    )
    
    # Join exploded people with title details
    exploded = exploded.join(
        titles_lookup,
        exploded.explodedTconst == titles_lookup.tconst,
        how="left"
    )
    
    # Aggregate main titles for each person as a list of structs
    main_titles = exploded.groupBy("nconst").agg(
        collect_list(
            struct(
                col("explodedTconst").alias("tconst"),
                col("title"),
                col("year")
            )
        ).alias("mainTitles")
    )
    
    # Join back to the original people_df and drop intermediate columns
    people_final = people_df.drop("knownForTitles", "knownForTitlesArray") \
        .join(main_titles, on="nconst", how="left")
    
    return people_final

# ---------------------- MONGODB WRITING ----------------------

def write_to_mongodb(df, collection_name, 
                     repartition=False, 
                     dim=10_000, 
                     db_name="imdbSpark"):
    """
    Write the given DataFrame to MongoDB.

    Args:
        df (DataFrame): The DataFrame to be written.
        collection_name (str): The target MongoDB collection name.
        repartition (bool, optional): Whether to repartition the data before writing. Defaults to False.
        dim (int, optional): Number of partitions if repartitioning is enabled. Defaults to 10,000.
    """
    logging.info(f"Writing collection '{collection_name}' to MongoDB ...")
    if not repartition:
        df.write.format("mongodb") \
            .mode("overwrite") \
            .option("database", db_name) \
            .option("collection", collection_name) \
            .save()
    else:
        logging.info(f"Writing on {dim} repartitions")
        df.repartition(dim).write.format("mongodb") \
            .mode("overwrite") \
            .option("database", db_name) \
            .option("collection", collection_name) \
            .save()




def main():
    """
    Main function to orchestrate data processing.

    - Initializes logging and Spark session.
    - Reads input datasets.
    - Processes and aggregates principals.
    - Prepares Movies, TV Series, and Shorts collections.
    - Enriches TV Series with episode details.
    - Processes the People collection.
    - Writes all collections to MongoDB.
    - Stops the Spark session.
    """
    logging.basicConfig(level=logging.INFO)
    spark = create_spark_session()
    #spark.sparkContext.setLogLevel("DEBUG")
    
    try:
        # Read input datasets
        title_basics, name_basics, title_episode, title_principals, title_ratings = read_datasets(spark)
        
        # Process principals and aggregate people per title
        aggregated_principals = process_principals(title_principals, name_basics)
        
        # Prepare the three title collections: Movies, TV Series, and Shorts
        movies_total, tv_series_total, shorts_total = prepare_title_collections(
            title_basics, aggregated_principals, title_ratings
        )
        
        # Enrich TV Series with episode details
        tv_series_total = add_episodes_to_tv_series(tv_series_total, title_episode, title_basics,title_ratings)
        
        # Write collections to MongoDB
        write_to_mongodb(movies_total, "movies", db_name="imdb") 
        write_to_mongodb(tv_series_total, "tvSeries", db_name="imdb")
        write_to_mongodb(shorts_total, "shorts", db_name="imdb")
        
        # Write People collection (using the name_basics dataset)
        # Process People collection to add structured main titles
        people_final = process_people(name_basics, title_basics)
        write_to_mongodb(people_final, "people", db_name="imdb")
        
    finally:
        spark.stop()
        logging.info("Spark session stopped.")



if __name__ == "__main__":
    main()
