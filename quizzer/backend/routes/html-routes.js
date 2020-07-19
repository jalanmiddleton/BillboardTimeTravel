const mysql = require("mysql")

module.exports = function(app, connection) {
  app.post("/", function(req, res) {
    let limit = req.body.songsper * req.body.playlists
    let query =  `SELECT uri
        ${req.body.popularity} * popularity / 100 + 
          ${req.body.highest} * (101 - MIN(idx)) / 100 + 
          ${req.body.weeks} * COUNT(*) / 87 -
          least(power(coalesce(tries, 0) / 5, 2), 1) AS points
    FROM
        billboard.tracks
            JOIN
        \`hot-100\` ON id = item_id
        LEFT JOIN billboard.quiz on (id = songid)
    WHERE
        uri IS NOT NULL and year(week) between ${req.body.start} and 
          ${req.body.end || req.body.start}
    GROUP BY id
    ORDER BY points DESC limit ${limit};`

    connection.query(query, function(err, data) {
      (err)? res.send(err) : res.json({tracks: data.map(x => x.uri)})
    })
  })

  app.post("/score", function(req, res) {
    let addby = req.body.correct ? 1 : 0;
    let idquery = `INSERT INTO quiz
      SELECT id, now(), 1, ${addby}  FROM tracks WHERE uri IN
      (${req.body.songs.map(x => `"${x.track.uri}"`).join(",")})
      ON DUPLICATE KEY UPDATE	 
        tries = tries + 1,
        correct = case when ${addby} = 1 then correct + 1 else max(correct - 2, 0) end,
        lastattempt = case when ${addby} = 1 then now() else lastattempt end`
    connection.query(idquery, function(err, data) {
      (err)? res.send(err) : res.json({ msg: "cool" })
    })
  })
}