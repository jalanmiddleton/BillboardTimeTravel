import $, { map } from "jquery";
import React from 'react';
import ReactDOM from 'react-dom';

export default class Quiz extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      playlists: null,
      tracks: null,
      score: null,
      index: -1,
      song: "",
      artist: "",
      playing: true
    }

    this.onSubmit = this.onSubmit.bind(this)
    this.onChange = this.onChange.bind(this)
    this.renderMenu = this.renderMenu.bind(this)
    this.playnext = this.playnext.bind(this)
    this.replaceList = this.replaceList.bind(this)
  }

  renderMenu(event) { 
    event.preventDefault()   

    let options = document.getElementById("playlists")
    let uri = options.children[options.selectedIndex]
              .getAttribute("uri").split(":").pop()

    return $.ajax({
      url: `https://api.spotify.com/v1/playlists/${uri}/tracks`,
      headers: this.props.auth
    }).then(result => {
      let newstate = Object.assign({}, this.state)
      newstate.tracks = this.shuffle(result)
      newstate.score = []
      return this.setState(newstate, this.playnext)
    }).catch(err => {
      console.log(err)
    })
  }

  async getplaylist(playlist_name, url) {
    url = url || `https://api.spotify.com/v1/me/playlists`

    const response = await $.ajax({
      url: url,
      headers: this.props.auth
    });
    let playlist = response.items.find(playlist_1 => playlist_1.name === playlist_name);
    
    if (playlist)
      return playlist;
    else if (response.next)
      return this.getplaylist(playlist_name, response.next);
    else
      return null;
  }
  
  // redundant with getplaylist
  async getPlaylists(playlists, url) {
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
      if (res.next) {
        return this.getPlaylists(playlists, res.next)     
      } else {
        return playlists
      }
    })
  }

  shuffle(playlist) {
    // I don't want to queue things up, just shuffle.
    let shuffled = []
    let unshuffled = playlist.items.slice()
    while (unshuffled.length > 0) {
      let rand = Math.floor(Math.random() * unshuffled.length)
      shuffled.push(unshuffled[rand])
      unshuffled.splice(rand, 1)
    }

    return shuffled
  }

  onChange(event) {
    let newstate = Object.assign({}, this.state)
    newstate[event.target.id] = event.target.value 
    this.setState(newstate)
  }

  onSubmit(event) {
    event.preventDefault()

    let songname = this.state.tracks[this.state.index].track.name.toLowerCase()
    songname = songname.split(" - ")[0]
    let reaction = ""
    let next = null

    if (this.state.song.toLowerCase() === songname) {
      reaction += "Song correct! "

      if (this.state.playing)
        this.props.player.togglePlay()

      next = () => {
        return new Promise(resolve => setTimeout(resolve, 2000))
                .then(() => {
                  document.getElementById("song")
                }).then(() => this.playnext(true))
      }
    } else {
      reaction += "Song incorrect! "
    }

    this.print(reaction, next)
  }

  async play({
    spotify_uri,
    playerInstance: {
      _options: {
        // getOAuthToken,
        id
      }
    }
  }) {
    try {
      await $.ajax({
        url: `https://api.spotify.com/v1/me/player/play?device_id=${id}`,
        type: 'PUT',
        data: JSON.stringify({ uris: [spotify_uri] }),
        headers: { 
          ...this.props.auth,
          'Content-Type': 'application/json'
        }
      });
    }
    catch (error) {
      console.log(error);
    }
  }

  async playnext(correct) {
    let newstate = { ...this.state };
    newstate.index += 1;
    newstate.playing = true;
    if (correct !== undefined)
      newstate.score.push(correct)
    this.setState(newstate);

    await this.play({
      playerInstance: this.props.player,
      spotify_uri: this.state.tracks[newstate.index].track.uri,
    });
  }

  async print(text, callback) {
    return ReactDOM.render(
      <span>{text}</span>,
      document.getElementById("answer"),
      callback
    )
  }

  replaceList(playlists) {
    let newstate = Object.assign({}, this.state)
    newstate.playlists = playlists.map((elem, idx) => 
      <option key={`${elem.name}_${idx}`} uri={elem.uri}>{elem.name}</option>
    )
    this.setState(newstate)
  }

  render() {
    // On first loading.
    if (this.state.playlists === null) {
      this.getPlaylists().then(this.replaceList)
      return (
        <div id="choose">Loading...</div>
      )

    // After songs are loaded.
    } else if (this.state.index === -1) {
      return (
        <form id="playlistlist" onSubmit={this.renderMenu}>      
          <label>Choose the playlist to quiz: </label><br />
          <select name="playlists" id="playlists">{this.state.playlists}</select><br />
          <button id="start">Start the Quiz!</button>
        </form>
      )

    // After a playlist is chosen.
    } else {
      let playmessage = this.state.playing ? "Playing..." : "Paused"
      return (
        <div id="quiz">                    
          <div id="state">{playmessage}</div>

          <Song onChange={this.onChange} onSubmit={this.onSubmit} />
          
          <button onClick={() => {
            this.props.player.togglePlay().then(() => {
              let newstate = Object.assign({}, this.state)
              newstate.playing = !newstate.playing
              this.setState(newstate)
            })}}>Pause</button>

          <button onClick={() => {
            let song = this.state.tracks[this.state.index].track.name 
            this.print(`Quitter! The song was ${song}.`,
              () => new Promise(resolve => setTimeout(resolve, 2000))
                      .then(() => this.playnext(false)))
          }}>Give up</button>

          <button onClick={() => {
            console.log(this.state.score)
            this.props.player.disconnect()
            ReactDOM.render(
              <End tracks={this.state.tracks} score={this.state.score} />,
              document.getElementById("root"))
          }}>Quit</button>

          <div id="answer"></div>
        </div>
      )
    }
  }
}

function Song(props) {
  return (
    <form onSubmit={props.onSubmit}>
      <label>
        Song Title:
        <input type="text" id="song" onChange={props.onChange} />
      </label>
      <input type="submit" value="Submit" />
    </form>
  )
}

class End extends React.Component {
  updatePlays(songs, iscorrect) {
    return fetch("http://localhost:3300/score", {
      method: "POST",
      mode: "cors",
      cache: 'no-cache', 
      credentials: 'same-origin', 
      headers: {
        'Content-Type': 'application/json'
      },
      redirect: 'follow', 
      referrerPolicy: 'no-referrer',   
      body: JSON.stringify({ songs: songs, 
                             correct: iscorrect })
    }).then((res) => {
      return res.json()
    }).then((res) => {
      console.log(res)
    }).catch(console.log)
  }

  render() {
    let correct = [], incorrect = []
    for (let i in this.props.score) {
      if (this.props.score[i] === true) {
        correct.push(this.props.tracks[i])
      } else {
        incorrect.push(this.props.tracks[i])
      }
    }

    this.updatePlays(correct, true)
    this.updatePlays(incorrect, false)

    // TODO: wrong but do more important stuff first
    let correctmessage = correct.length > 0 ?
      `You got ${correct.length} songs correct:\n\t` + map(correct, x => x.track.name).join("\n\t") :
      "You got NOTHING correct. 😡"

    let incorrectmessage = incorrect.length > 0 ?
      `You got ${incorrect.length} songs incorrect:\n\t` + map(incorrect, x => x.track.name).join("\n\t") :
      "You got them all, hot stuff. 😳"
     
    return (
      <div id="results">
        <h4>Game Over!</h4>
        <div id="correct">{correctmessage}</div>
        <div id="incorrect">{incorrectmessage}</div>
      </div>
    )
  }
}

/* <label>
      Song Artist:
      <input type="text" name="artist" onChange={props.onChange} />
    </label> */