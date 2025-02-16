

// Select the database to use.
use('imdb');
db.movies.aggregate([
    // 1. Process movies: unwind the people array
    {
      $unwind: "$people"
    },
    // 2. Filter out movies with null ratings
    {
      $match: { "rating.averageRating": { $ne: null } }
    },
    // 3. Project the needed fields from movies
    {
      $project: {
        nconst: "$people.nconst",
        primaryName: "$people.name",
        rating: "$rating.averageRating",
        type: { $literal: "movie" }
      }
    },
    // 4. Union with the tvSeries collection
    {
      $unionWith: {
        coll: "tvSeries",
        pipeline: [
          // Unwind the people array in tvSeries
          { $unwind: "$people" },
          // Filter out TV series with null ratings
          { $match: { "rating.averageRating": { $ne: null } } },
          // Project the fields from tvSeries
          { $project: {
              nconst: "$people.nconst",
              primaryName: "$people.name",
              rating: "$rating.averageRating",
              type: { $literal: "tvSeries" }
          }}
        ]
      }
    },
    // 5. Group by person identifier to aggregate counts and average ratings
    {
      $group: {
        _id: "$nconst",
        primaryName: { $first: "$primaryName" },
        // Count movies and tv series appearances separately
        movieCount: { $sum: { $cond: [{ $eq: ["$type", "movie"] }, 1, 0] } },
        tvSeriesCount: { $sum: { $cond: [{ $eq: ["$type", "tvSeries"] }, 1, 0] } },
        // Overall title count (movies + tv series)
        overallCount: { $sum: 1 },
        // Average rating across all titles
        avgRating: { $avg: "$rating" }
      }
    },
    // 6. Sort the results by overall count (descending) and then by average rating (descending)
    {
      $sort: { overallCount: -1, avgRating: -1 }
    },
    // 7. Project the final output format
    {
      $project: {
        _id: 0,
        nconst: "$_id",
        primaryName: 1,
        movieCount: 1,
        tvSeriesCount: 1,
        overallCount: 1,
        avgRating: 1
      }
    }
  ])
  