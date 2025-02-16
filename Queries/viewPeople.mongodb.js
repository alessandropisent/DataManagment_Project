use("imdb");
db.createView(
    "peopleWithTitles",  // Name of the view
    "people",            // Source collection
    [
      // Lookup movies where this person is listed in the people array
      {
        $lookup: {
          from: "movies",
          let: { personId: "$nconst" },
          pipeline: [
            { $match: { $expr: { $in: ["$$personId", "$people.nconst"] } } },
            { $project: { _id: 0, tconst: 1, Title: 1, startYear: 1 } }
          ],
          as: "movies"
        }
      },
      // Lookup TV series where this person is listed in the people array
      {
        $lookup: {
          from: "tvSeries",
          let: { personId: "$nconst" },
          pipeline: [
            { $match: { $expr: { $in: ["$$personId", "$people.nconst"] } } },
            { $project: { _id: 0, tconst: 1, Title: 1, startYear: 1, endYear: 1 } }
          ],
          as: "tvSeries"
        }
      },
      // Lookup shorts where this person is listed in the people array
      {
        $lookup: {
          from: "shorts",
          let: { personId: "$nconst" },
          pipeline: [
            { $match: { $expr: { $in: ["$$personId", "$people.nconst"] } } },
            { $project: { _id: 0, tconst: 1, Title: 1, startYear: 1 } }
          ],
          as: "shorts"
        }
      },
      // Combine all titles into one field
      {
        $addFields: {
          allTitles: {
            $concatArrays: [ "$movies", "$tvSeries", "$shorts" ]
          }
        }
      },
      // Remove the intermediate arrays for a cleaner result
      {
        $project: {
          movies: 0,
          tvSeries: 0,
          shorts: 0
        }
      }
    ]
  )
  