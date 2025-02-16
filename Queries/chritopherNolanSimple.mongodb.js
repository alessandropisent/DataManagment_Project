use("imdb");
db.movies.find(
    { "people": { $elemMatch: { category: "director", name: "Christopher Nolan" } } },
    {"people":0}
  ).sort({ "rating.averageRating": -1 })
  