const express = require('express')
const app = express()
const PORT = 3300
const mysql = require('mysql')
const secrets = require('./secrets.js')

const connection = mysql.createConnection({
  host: "localhost",
  user: "root",
  password: secrets.mysqlpassword,
  database: "billboard"
})

connection.connect(function(err) {
  (err)? console.log(err): console.log("connection success");
})

require("./routes/html-routes.js")(app, connection)
var server = app.listen(PORT, () => {
  console.log("App listening at http://%s:%s", 
              server.address().address, server.address().port )
})