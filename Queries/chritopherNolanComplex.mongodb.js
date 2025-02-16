use("imdb");
db.movies.aggregate([
    // Match movies that have Christopher Nolan as a director
    { 
      $match: { 
        "people": { 
          $elemMatch: { category: "director", name: "Christopher Nolan" } 
        } 
      } 
    },
    // Compute Nolan's ordering value
    { 
      $addFields: {
        nolanOrdering: {
          $min: {
            $map: {
              input: {
                $filter: {
                  input: "$people",
                  as: "p",
                  cond: {
                    $and: [
                      { $eq: [ "$$p.category", "director" ] },
                      { $eq: [ "$$p.name", "Christopher Nolan" ] }
                    ]
                  }
                }
              },
              as: "p",
              in: "$$p.ordering"
            }
          }
        }
      }
    },
    // Filter the people array to only include entries up to Nolan's ordering
    { 
      $project: {
        title: 1,
        rating: 1,
        people: {
          $filter: {
            input: "$people",
            as: "p",
            cond: { $lte: [ "$$p.ordering", "$nolanOrdering" ] }
          }
        }
      }
    }
  ]).sort({ "rating.averageRating": -1 })
  