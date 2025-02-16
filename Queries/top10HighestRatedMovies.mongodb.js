use('imdb');
db.movies.find(
    { "rating.averageRating": { $gte:9.0 }, "rating.numVotes": { $gte: 1000 } },
    //{ "title": 1, "rating.averageRating": 1, "rating.numVotes": 1 }
  )
  .sort({ "rating.averageRating": -1 })
  .limit(10)