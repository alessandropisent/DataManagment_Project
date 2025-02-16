use("imdb");

db.tvSeries.aggregate([
    // Match the Game of Thrones series
    {
      $match: { title: "Game of Thrones" }
    },
    // Unwind the episodes array so that we can sort and filter individual episodes
    {
      $unwind: "$episodes"
    },
    // Filter out episodes that do not have a rating
    {
      $match: { "episodes.rating.averageRating": { $exists: true } }
    },
    // Sort episodes by rating in descending order
    {
      $sort: { "episodes.rating.averageRating": -1 }
    },
    // Limit to the top 10 episodes
    {
      $limit: 10
    },
    // Reshape the output to display relevant episode details
    {
      $project: {
        _id: 0,
        Title: "$episodes.Title",
        Season: "$episodes.ordering.Season",
        Episode: "$episodes.ordering.Episode",
        Rating: "$episodes.rating.averageRating",
        Votes: "$episodes.rating.numVotes",
        Runtime: "$episodes.runtimeMinutes",
        Year: "$episodes.year"
      }
    }
  ])
  
