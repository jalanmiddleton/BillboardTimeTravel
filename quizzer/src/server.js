const express = require('express')
const app = express()
const PORT = 3300
const mysql = require('mysql')
const secrets = require('secrets.js')

const connection = mysql.createConnection({
  host: "localhost",
  user: "root",
  password: secrets.password,
  database: "billboard"
})

var server = app.listen(PORT, () => {
  var host = server.address().address
  var port = server.address().port 
  console.log("App listening at http://%s:%s", host, port)
})