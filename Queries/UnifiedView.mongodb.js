// Select the database to use.
use('imdb');

// First, create a view that unions movies, tvSeries, and shorts
db.createView("titles", "tvSeries", [
    {
      $addFields:{
          titleType: { $literal: "tvSeries" }
      }
    },
    // Union with shorts
    { 
      $unionWith: {
        coll: "shorts",
        pipeline: [
          {
            $addFields: { startYear: "$year",// Rename "year" to "startYear"
              titleType: { $literal: "short" },
            } 
          },
          {
            $project: { 
              
              year: 0
              
            } 
          }
        ]
      }
    },
    // union movies
    {
      $unionWith: {
        coll: "movies",
        pipeline: [
          {
            $addFields: { 
              startYear: "$year",
              titleType: { $literal: "movies" },
             } // Rename "year" to "startYear"
          },
          {
            $project: { 
              
              year: 0
             } // Remove old "year" field
          }
        ]
      }
    },
  ])
  