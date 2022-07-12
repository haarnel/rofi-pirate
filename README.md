<div align="center">

# 🏴‍☠ Rofi Pirate
  
![](assets/logo.png)

  
</div>  

Rofi module for searching torrents using Jackett API. You can also instantly play media files without having to leave the Rofi menu. The project is still in beta.



https://user-images.githubusercontent.com/83361542/178555960-8ba45500-1705-4036-a5c6-2aed8b38be11.mp4

Rofi theme I use: [Click](https://github.com/haarnel/dotfiles/blob/bspwm-daily/.config/rofi/themes/main.rasi)

## Requirements

1. Streaming torrent client: [Peerflix](https://github.com/mafintosh/peerflix) (to play media files without downloading it first)
2. qBittorent (optional)
3. Nerd Fonts

## Setup process

1. First, you need a running instance of Jackett and install Peerflix

```shell
# Arch Linux users
yay -S jackett-bin
systemctl start jackett.service # then go to http://localhost:9117/
# Or Docker image
docker pull linuxserver/jackett
# Peerflix install
npm install -g peerflix
```

2. Set up your indexers through the dashboard and also obtain an API key from there.

3. Install rofi-python package.

```shell
pip install rofi-pirate
```

4. Place the configuration file under ```~/.config/rofi_pirate/config.json```. **Don't forget** to specify your API key.

Config example:

```json
{
  "JACKETT_ENDPOINT": "http://127.0.0.1:9117",
  "JACKETT_APIKEY": "<API_KEY>", 
  "SEARCH_LIMIT": 25,
  "PEERFLIX_CMD": "peerflix -t -k -a",
  "PEERFLIX_CACHE": "~/Downloads/Torrents",
  "HISTORY_CACHE": "~/.config/rofi_pirate/history.db",
}
```

## TODO

- [ ] Dynamic indexer configuration.
- [ ] Ability to preview torrent images (movie/music covers).
