import React from 'react';

//import ReactDOM from 'react-dom';

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
      playlists: 5,
      name: null
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
    
    Promise.all([this.getPlaylists(), this.getTracks()])
    .then((res) => {
      this.replacePlaylists(...res)
    }).then(console.log).catch((err) => {
      console.log(err)
    })
  }

  getTracks() {
    return fetch("http://localhost:3300", {
      method: "POST",
      mode: "cors",
      cache: 'no-cache', 
      credentials: 'same-origin', 
      headers: {
        'Content-Type': 'application/json'
      },
      redirect: 'follow', 
      referrerPolicy: 'no-referrer',   
      body: JSON.stringify(this.state)
    }).then((response) => {
      return response.json()
    }).then(res => {
      return res.tracks
    })
  } 

  getPlaylists(url, playlists) {
    if (!url) {
      url = "https://api.spotify.com/v1/me/playlists"
    }
    if (!playlists) {
      playlists = []
    }

    return fetch(url, {
      method: "GET",
      headers: {...this.props.auth,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    }).then(res => {
      return res.json()
    }).then(res => {
      playlists = playlists.concat(res.items.filter(item => item.name.startsWith("BB")))
      if (playlists.length >= this.state.playlists) {
        return playlists.slice(0, this.state.playlists)
      } else {
        return this.getPlaylists(res.next, playlists)
      }
    })
  }

  replacePlaylists(playlists, songs) {
    if (!playlists.length || !songs.length)
      return "Done!"

    return fetch(`https://api.spotify.com/v1/playlists/${playlists[0].id}/tracks`, {
      method: "PUT",
      headers: {...this.props.auth,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        "uris": songs.slice(0, 20)
      })
    }).then(res => {
      if (this.state.name) {
        let number = this.state.playlists - songs.length / this.state.songsper + 1
        return fetch(`https://api.spotify.com/v1/playlists/${playlists[0].id}`, {
          method: "PUT",
          headers: {
            ...this.props.auth,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name: `BB ${number}: ${this.state.name}`
          })
        })
      }
    }).then(res => {
      return this.replacePlaylists(playlists.slice(1), songs.slice(20))
    })
  }

  render() {
    return (
      <form onSubmit={this.onSubmit}>
        <em>Range</em><br />
        <label>Start Year: </label>        
        <input type="number" id="start" min="1957" max="2020" onChange={this.onFieldChange} />
        <br />

        <label>End Year: </label>
        <input type="number" id="end" min="1957" max="2020" onChange={this.onFieldChange} />
         (leave blank for single year)
        <br />
        <br />

        <em>Playlist Details </em><br />        
        <label>Name </label>
        <input type="text" id="name" onChange={this.onFieldChange} />
        <br />

        <label>Songs Per Playlist </label>
        <input type="number" id="songsper" onChange={this.onFieldChange} />
        <br />

        <label>Number of Playlists </label>
        <input type="number" id="playlists" onChange={this.onFieldChange} />
        <br />
        <br />
        
        <em>Weights</em><br />
        <label>Spotify Popularity </label>
        <input type="number" id="popularity" onChange={this.onFieldChange} />
        <br />

        <label>Billboard Weeks </label>
        <input type="number" id="weeks" onChange={this.onFieldChange} />
        <br />

        <label>Billboard Highest </label>
        <input type="number" id="highest" onChange={this.onFieldChange} />
        <br />
        <br />
      <input type="submit" value="Submit" />
    </form>
    )
  }
}
