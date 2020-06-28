const mysql = require("mysql")

module.exports = function(app, connection) {
  app.get("/", function(req, res) {
    // let query =  `SELECT 
    //     uri,
    //     popularity,
    //     MAX(idx),
    //     COUNT(*),
    //     ${this.state.popularity} * popularity / 100 + 
    //       ${this.state.highest} * (101 - MAX(idx)) / 100 + 
    //       ${this.state.weeks} * COUNT(*) / 87 AS points
    // FROM
    //     billboard.tracks
    //         JOIN
    //     \`hot-100\` ON id = item_id
    // WHERE
    //     uri IS NOT NULL and year(week) between ${this.state.start} and 
    //       ${this.state.end || this.state.start}
    // GROUP BY id
    // ORDER BY points DESC limit ${limit};`
    let query = "SELECT * FROM tracks limit 100;"

    connection.query(query, function(err, data) {
      (err)? res.send(err) : res.json({users: data})
    })
  })
}