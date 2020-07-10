const mysql = require("mysql")

module.exports = function(app, connection) {
  app.post("/", function(req, res) {
    let limit = req.body.songsper * req.body.playlists
    let query =  `SELECT uri FROM (SELECT 
        uri,
        popularity,
        MIN(idx),
        COUNT(*),
        ${req.body.popularity} * popularity / 100 + 
          ${req.body.highest} * (101 - MIN(idx)) / 100 + 
          ${req.body.weeks} * COUNT(*) / 87 AS points
    FROM
        billboard.tracks
            JOIN
        \`hot-100\` ON id = item_id
    WHERE
        uri IS NOT NULL and year(week) between ${req.body.start} and 
          ${req.body.end || req.body.start}
    GROUP BY id
    ORDER BY points DESC limit ${limit}) tracks;`

    connection.query(query, function(err, data) {
      (err)? res.send(err) : res.json({tracks: data.map(x => x.uri)})
    })
  })
}