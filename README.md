**Table of Contents**
- [Project Overview](#project-overview)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Data Processing Workflow](#data-processing-workflow)
- [MongoDB Output](#mongodb-output)



## Project Overview
This project focuses on processing IMDb-related data stored in TSV files, transforming it into structured DataFrames using Apache Spark, and writing the results to a MongoDB database. The project includes the following key functionalities:

- **Data Schema Definition**: Defines explicit schemas for different IMDb datasets (e.g., title basics, name basics, title ratings).
- **Data Reading**: Reads the datasets into Spark DataFrames from TSV files.
- **Data Processing**: Aggregates, enriches, and filters the data as needed for movies, TV series, shorts, and people (actors, crew, etc.).
- **MongoDB Integration**: Writes the processed data to MongoDB collections.
    

## Dependencies

This project requires the following libraries:
- **Apache Spark**: Used for distributed data processing.
- **MongoDB Spark Connector**: Allows interaction with MongoDB.
- **Python Libraries**:
    - `logging` for logging and debugging
    - `pyspark` for Spark DataFrame operations

You will need a running instance of MongoDB locally or remotely to store the results.

## Usage

To run the project:

1. **Install Spark**: Ensure Apache Spark is installed. You can follow the [official Spark installation guide](https://spark.apache.org/docs/latest/index.html).
2. **Install MongoDB**: Set up MongoDB either locally or use a remote database.
3. **Clone the Repository**:

```bash
git clone <your-repository-url>
cd <your-repository-directory>
```
    
4. **Install Required Python Packages**: Ensure you have the necessary dependencies by installing them via pip:

```python
pip install pyspark
```

5. **Download the dataset**: Download the dataset
```bash
cd Datasets
./download.sh
./uncompress.sh
```

6. **Run the Main Script**: Execute the Python script to start the processing:
      
```bash
python3 imdb_data_processing.py
```
    



## Data Processing Workflow

The project follows a structured data pipeline:

1. **Spark Session Creation**: A Spark session is created and configured to read data from TSV files and connect to MongoDB.
2. **Data Reading**: The following datasets are read with predefined schemas:
    - `title.basics`
    - `name.basics`
    - `title.episode`
    - `title.principals`
    - `title.ratings`
        
3. **Data Transformation**:
    
    - **Process Principals**: Joins `title.principals` with `name.basics` to enrich titles with cast and crew details.
    - **Prepare Collections**: Filters and transforms the data into three primary collections (Movies, TV Series, Shorts).
    - **Enrich TV Series with Episodes**: Adds episode details for TV Series.
    - **Process People**: Converts the `knownForTitles` field into structured arrays for people (actors, directors, etc.).
        
10. **Data Writing to MongoDB**: The processed data is saved into MongoDB collections:

    - `movies`
    - `tvSeries`
    - `shorts`
    - `people`

## MongoDB Output

Once the data is processed, the following collections will be created in MongoDB:

1. **movies**: Contains processed data related to movies, including title, genre, year, and ratings.
2. **tvSeries**: Contains TV series data along with episode details and ratings.
3. **shorts**: Contains data for short films.
4. **people**: Contains people (actors, directors, etc.) data, enriched with the titles they are known for.
    
Make sure MongoDB is running on the specified connection URI (`mongodb://localhost:27017/imdb`) before running the script