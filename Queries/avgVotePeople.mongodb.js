// Select the database to use.

use('imdb')
db.titles.aggregate([
  // 1. Filter out titles without ratings
  {
    $match: { "rating.averageRating": { $ne: null } }
  },
  // 2. Unwind the people array
  {
    $unwind: "$people"
  },
  // 3. Filter only actors and actresses
  {
    $match: {
      "people.category": { $in: ["actor", "actress"] }
    }
  },
  // 4. Group by actor/actress and titleType to compute per-type averages
  {
    $group: {
      _id: {
        actorName: "$people.name",
        titleType: "$titleType"
      },
      avgRating: { $avg: "$rating.averageRating" },
      numTitles: { $sum: 1 }
    }
  },
  // 5. Group again by actorName to compute overall average and weighted importance
  {
    $group: {
      _id: "$_id.actorName",
      overallAvgRating: { $avg: "$avgRating" },
      totalTitles: { $sum: "$numTitles" },
      perTitleType: {
        $push: {
          titleType: "$_id.titleType",
          avgRating: { $round: ["$avgRating", 2] },
          numTitles: "$numTitles"
        }
      }
    }
  },
  // 6. Add the weighted importance field
  {
    $addFields: {
      weightedImportance: { $multiply: ["$overallAvgRating", "$totalTitles"] }
    }
  },
  // 7. Sort by weighted importance in descending order
  {
    $sort: { weightedImportance: -1 }
  },
  // 8. Limit to top 10 people
  {
    $limit: 10
  },
  // 9. Format output
  {
    $project: {
      _id: 0,
      actorName: "$_id",
      overallAvgRating: { $round: ["$overallAvgRating", 2] },
      totalTitles: 1,
      weightedImportance: 1,
      perTitleType: 1
    }
  }
]);

