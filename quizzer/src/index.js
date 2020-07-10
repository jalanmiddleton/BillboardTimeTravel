import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import secrets from './secrets.js';
import Quiz from './Quiz.js';
import Playlister from './Playlister.js';

// https://levelup.gitconnected.com/how-to-build-a-spotify-player-with-react-in-15-minutes-7e01991bc4b6
// Get the hash of the url
const hash = window.location.hash
  .substring(1)
  .split("&")
  .reduce(function(initial, item) {
    if (item) {
      var parts = item.split("=");
      initial[parts[0]] = decodeURIComponent(parts[1]);
    }
    return initial;
  }, {});
window.location.hash = "";

class Login extends React.Component {
  render() {
    let auth_url = 'https://accounts.spotify.com/authorize?client_id=' + secrets.client_id +
      '&redirect_uri=' + encodeURIComponent(secrets.redirect_uri) +
      '&scope=' + encodeURIComponent(
                    "streaming,user-read-playback-state," +
                    "user-read-email,user-read-private," +
                    "playlist-read-collaborative") +
      '&response_type=token&show_dialog=true'
    return (
    <a 
      className="btn btn--loginApp-link"
      href={auth_url}
    >
      Login to Spotify
    </a>)
  }
}

class Choose extends React.Component {
  render() {
    let auth = {
      'Authorization': 'Bearer ' + hash.access_token
    }
    return (
      <div>
        <button onClick={() => {
          setupPlayer().then(player => {
            if (player) {
              ReactDOM.render(
                <Quiz player={player} auth={auth} />,
                document.getElementById('root')
              );
            } else {
              // When failure...
            }
          });
        }}>Quiz</button><br />
        <button onClick={() => {
          ReactDOM.render(
            <Playlister auth={auth} />,
            document.getElementById("root")
          )
        }}>Make New Playlists</button>
      </div>
    )
  }
}

window.onSpotifyWebPlaybackSDKReady = () => {
  if (hash.access_token) {   
    ReactDOM.render(
      <Choose />,
      document.getElementById('root')
    );
  }
};

function setupPlayer() {
  const player = new window.Spotify.Player({
    name: 'Web Playback SDK Quick Start Player',
    getOAuthToken: cb => { cb(hash.access_token); },
    volume: .33
  });

  // Error handling
  player.addListener('initialization_error', ({ message }) => { console.error(message); });
  player.addListener('authentication_error', ({ message }) => { console.error(message); });
  player.addListener('account_error', ({ message }) => { console.error(message); });
  player.addListener('playback_error', ({ message }) => { console.error(message); });
  player.addListener('player_state_changed', state => { console.log(state); });
  player.addListener('ready', ({ device_id }) => {
    console.log('Ready with Device ID', device_id);
  });
  player.addListener('not_ready', ({ device_id }) => {
    console.log('Device ID has gone offline', device_id);
  });

  // Connect to the player!
  return player.connect().then(success => {
    return success ? player : null;
  })
}

if (!hash.access_token) 
  ReactDOM.render(<Login />, document.getElementById("root"))