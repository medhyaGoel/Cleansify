[CLEANSIFY](cleansify.onrender.com)! 
Link - cleansify.onrender.com
Swap explicit songs in your Spotify playlists with their clean counterparts at the click of a button.

Crafted with Python (Flask), HTML/CSS/JS, and the Spotify Web API. Deployed on Render.

To run locally...
1. Create app on Spotify Developer Dashboard. The redirect uri should be "localhost:port_number/callback/q" without the quotes.
2. Create .env file and update appropriate redirect uri (this value should be "localhost:port_number" without the quotes), client id, client secret, and app secret values as chosen in previous step.
3. Run server.
4. Access the site at localhost:port_number
