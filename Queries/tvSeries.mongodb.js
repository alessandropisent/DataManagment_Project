// Select the database to use.
use('imdbSpark');

db.tvSeries.aggregate([
    // Unwind the episodes array to process each episode individually
    { $unwind: "$episodes" },
    
    // Group by TV series title and calculate average episode runtime and episode count
    { $group: {
        _id: "$Title",
        avgEpisodeRuntime: { $avg: "$episodes.runtime" },
        episodeCount: { $sum: 1 }
    }},
    
    // Optionally, sort the TV series by the average episode runtime
    { $sort: { avgEpisodeRuntime: -1 } }
  ])
  