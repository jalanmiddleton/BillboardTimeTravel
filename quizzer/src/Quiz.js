import $ from "jquery";
import React from 'react';
import ReactDOM from 'react-dom';

export default class Quiz extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      index: -1,
      song: "",
      artist: "",
    }

    this.onSubmit = this.onSubmit.bind(this)
    this.onChange = this.onChange.bind(this)
    this.renderMenu = this.renderMenu.bind(this)
    this.playnext = this.playnext.bind(this)
  }

  onChange(event) {
    let newstate = Object.assign({}, this.state)
    newstate[event.target.name] = event.target.value 
    this.setState(newstate)
  }

  onSubmit(event) {
    event.preventDefault()

    console.log(this.state.song)
    console.log(this.state.playlist[this.state.index].track.name.toLowerCase())
    console.log(this.state.playlist.slice(0, 5).map(x => x.track.name)) 
    console.log(this.state.index)

    let songname = this.state.playlist[this.state.index].track.name.toLowerCase()
    songname = songname.split(" - ")[0]

    let reaction = ""
    let next = null
    if (this.state.song.toLowerCase() === songname) {
      reaction += "Song correct! "
      this.props.player.togglePlay()
      next = (res) => {
        return new Promise(resolve => setTimeout(resolve, 2000))
                .then(this.playnext)
      }
    } else {
      reaction += "Song incorrect! "
    }

    ReactDOM.render(
      <span>{reaction}</span>,
      document.getElementById("answer"),
      next
    )
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

  shufflePlaylist(playlist) {
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

  async playnext() {
    let newstate = { ...this.state };
    newstate.index += 1;
    await this.play({
      playerInstance: this.props.player,
      spotify_uri: this.state.playlist[newstate.index].track.uri,
    });
    this.setState(newstate);
  }

  renderMenu() {    
    this.getplaylist("Quizzable").then(result => {
      return $.ajax({
        url: `https://api.spotify.com/v1/playlists/${result.id}/tracks`,
        headers: this.props.auth
      })
    }).then(result => {
      return this.setState({
        playlist: this.shufflePlaylist(result),
        index: -1,
        song: "",
        artist: "",
      }, this.playnext)
    }).catch(err => {
      console.log(err)
    })
  }

  render() {
    if (this.state.index === -1)
      return (
        <button id="start" onClick={this.renderMenu}>
          Start the Quiz!
        </button>
      )
    else 
      return (
        <Song onChange={this.onChange} onSubmit={this.onSubmit} />
      )
  }
}

function Song(props) {
  return (<div><form onSubmit={props.onSubmit}>
    <label>
      Song Artist:
      <input type="text" name="artist" onChange={props.onChange} />
    </label>
    <label>
      Song Title:
      <input type="text" name="song" onChange={props.onChange} />
    </label>
    <input type="submit" value="Submit" />
    </form><div id="answer"></div></div>)
}