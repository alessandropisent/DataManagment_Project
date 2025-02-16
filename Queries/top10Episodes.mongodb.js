use("imdb");
db.tvSeries.aggregate([
    // Step 1: Filter TV series with at least 10,000 votes
    {
      $match: { "rating.numVotes": { $gte: 10000 } }
    },
    // Step 2: Sort TV series by average rating in descending order
    {
      $sort: { "rating.averageRating": -1 }
    },
    // Step 3: Limit to the top 10 TV series
    {
      $limit: 10
    },
    // Step 4: Unwind episodes to sort them individually
    {
      $unwind: "$episodes"
    },
    // Step 5: Sort episodes by rating (highest first)
    {
      $sort: { "episodes.rating.averageRating": -1 }
    },
    // Step 6: Group back into the TV series structure, keeping only the top 10 episodes
    {
      $group: {
        _id: "$_id", // Group by TV series ID
        tconst: { $first: "$tconst" },
        title: { $first: "$title" },
        originalTitle: { $first: "$originalTitle" },
        isAdult: { $first: "$isAdult" },
        startYear: { $first: "$startYear" },
        endYear: { $first: "$endYear" },
        runtimeMinutes: { $first: "$runtimeMinutes" },
        genres: { $first: "$genres" },
        //people: { $first: "$people" },
        rating: { $first: "$rating" },
        episodes: { $push: "$episodes" }
      }
    },
    // Step 7: Keep only the top 10 episodes per series
    {
      $project: {
        _id: 1,
        tconst: 1,
        title: 1,
        originalTitle: 1,
        isAdult: 1,
        startYear: 1,
        endYear: 1,
        runtimeMinutes: 1,
        genres: 1,
        people: 1,
        rating: 1,
        episodes: { $slice: ["$episodes", 10] } // Limit episodes to 10 per TV series
      }
    }
  ])
  