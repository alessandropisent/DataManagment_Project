// Select the database to use.
use('imdb');

db.movies.aggregate([
    // Unwind the genres array so that each genre is processed individually
    { $unwind: "$genres" },
    
    // Group by each genre and calculate the average rating and total count
    { $group: {
        _id: "$genres",
        avgRating: { $avg: "$rating.averageRating" },
        totalMovies: { $sum: 1 }
    }},
    
    // Sort genres by average rating in descending order
    { $sort: { avgRating: -1 } }
  ])
