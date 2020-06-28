import React from 'react';
import secrets from './secrets.js';

//import ReactDOM from 'react-dom';

const mysql = require('mysql')

/*
  When selected:
  1. Start year
  2. End year inclusive (if empty, only get start year).
  3. Weights
  3.1 Spotify popularity (S) [1]
  3.2 Weeks on Billboard (W) [1]
  3.3 Highest position (P) [1]
    [3.1]*S/100 + [3.2]*W/87 + [3.3]*(101-P)/100
  4. Songs per playlist
  5. # of playlists 

  Submit -> Run MySQL Query -
*/

// 87 weeks, Imagine Dragons,	"Radioactive"
export default class Playlister extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      start: 1990,
      end: 0,
      popularity: 1,
      weeks: 1,
      highest: 1,
      songsper: 20,
      playlists: 5
    }

    this.onFieldChange = this.onFieldChange.bind(this)
    this.onSubmit = this.onSubmit.bind(this)
  }

  onFieldChange(event) {
    let newstate = Object.assign({}, this.state)
    newstate[event.target.id] = event.target.value
    this.setState(newstate)
  }

  onSubmit(event) {
    event.preventDefault()
    
    let limit = this.state.songsper * this.state.playlists;
    let query =  `SELECT 
        uri,
        popularity,
        MAX(idx),
        COUNT(*),
        ${this.state.popularity} * popularity / 100 + 
          ${this.state.highest} * (101 - MAX(idx)) / 100 + 
          ${this.state.weeks} * COUNT(*) / 87 AS points
    FROM
        billboard.tracks
            JOIN
        \`hot-100\` ON id = item_id
    WHERE
        uri IS NOT NULL and year(week) between ${this.state.start} and 
          ${this.state.end || this.state.start}
    GROUP BY id
    ORDER BY points DESC limit ${limit};`

    let connection = mysql.createConnection({
      host: 'localhost', user: 'root', password: secrets.mysqlpass, 
      database: 'billboard'
    })
    connection.connect()
    connection.query(query, (error, results, fields) => {
      if (error) throw error;
      console.log(results[0])
    })
  }

  render() {
    return (
      <form onSubmit={this.onSubmit}>
        <em>Range</em><br />
        <label>Start Year: </label>        
        <input type="number" id="start" min="1957" max="2020" value="1990" onChange={this.onFieldChange} />
        <br />

        <label>End Year: (leave blank for single year) </label>
        <input type="number" id="end" min="1957" max="2020" onChange={this.onFieldChange} />
        <br />
        <br />

        <em>Weights</em>Weights<br />
        <label>Spotify Popularity </label>
        <input type="number" id="popularity" value="1" onChange={this.onFieldChange} />
        <br />

        <label>Billboard Weeks </label>
        <input type="number" id="weeks" value="1" onChange={this.onFieldChange} />
        <br />

        <label>Billboard Highest </label>
        <input type="number" id="highest" value="1" onChange={this.onFieldChange} />
        <br />
        <br />

        <em>Playlist Details </em><br />
        <label>Songs Per Playlist </label>
        <input type="number" id="songsper" value="20" onChange={this.onFieldChange} />
        <br />

        <label>Number of Playlists </label>
        <input type="number" id="playlists" value="5" onChange={this.onFieldChange} />
        <br />
      <input type="submit" value="Submit" />
    </form>
    )
  }
}
