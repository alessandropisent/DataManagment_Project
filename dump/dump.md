## To dump the db

mongodump --db imdb --gzip --out dump/`date +"%Y-%m-%d"`

## To restore the db

mongorestore --host localhost:27017 --gzip --nsInclude="imdb.*" --db imdbRestored dump/<date>/imdb