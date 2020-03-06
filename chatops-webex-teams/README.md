## Webex Teams bot for network automation | ChatOps 
### Technology notes
A bot is usually an entity in a messaging platform (like Webex Teams, Slack, Telegram) which is handled by a software application. There are two main ways to use a bot:  
* Notifications only (one-way communication) - bots send messages from the application but do not participate in the conversation and don't analyze incoming messages from other participants
* Conversational bots (two-way communication) - bots analyze incoming messages from humans, perform an action and reply back. When conversational bots pull some data from or even manage infrastructure (e.g. networks), it's usually called **ChatOps**.  

There are two main approaches to build conversational bots:
* Natural Language Processing (NLP) - uses Machine Learning to understand the intent or meaning behind human messages, hence humans can use plain English to communicate with the bot. You could use some existing NLP solution (e.g. [DialogFlow](https://dialogflow.com/) from Google) or build your own.
* Text parsing - it does not involve Machine learning and usually requires humans to communicate with the bot in a certain way, thus creating a special "CLI" for the bot. This approach is quite hard to maintain, because humans are not a reliable input source. To make it more reliable, a developer could add handling of capitalization, extra whitespaces, potentially even tokenization of the words (so `messages` and `message` is the same thing). This approach may also involve a bunch of regular expressions.

My opinion: NLP is interesting, but introduces complexity and cost. Also understanding a specialized text (e.g. technical language) is a harder task than general language (because cloud services are usually trained on general language snippets), so your success may vary.  
CLI approach adds a lot of maintenance on the developer side. You also need good documentation and user training so they are familiar with bot CLI.  
On top of that a messaging platform usually has limitations on input and output formatting: no forms to handle inputs, no tables, no JavaScript, limit on max number of symbols, etc.  
Personally, I think building a web application is a better time investment most of the time. On a web page you can have forms with dropdowns, client and server-side validation, no limits how to display output, you can use JavaScript to build any user experience you want AND your users will not need to learn another CLI.

Another thing to consider is an actual software architecture for your bot. Typical ways to get user messages:
* Webhooks (usually HTTP POST). This is the most popular approach. Either in the platform GUI or via API you register a public endpoint to receive notifications about new messages, which then can be processed by your web app. Such bots are a great fit for Serverless, where additional instances could be autoscaled by the cloud platform based on the usage and the lifetime of the request-response cycle is low
* Long polling - periodically an application asks a messenger service about the latest messages. Usually this approach is not the best for real-time interaction. 
* WebSockets - an application establishes a WebSockets session to a messenger WebSockets listener and new messages are being streamed over this session.

However, with Webhooks in ChatOps there is usually a problem. Very often a cloud service (publically hosted) doesn't have a way to initiate a connection to your infrastructure (especially network infrastructure). To solve this you need to use some reverse proxy/tunneling. Here are popular options:
* [frp](https://github.com/fatedier/frp) - open-source reverse proxy. You put a server on some publicly accessible machine, while the client will run alongside the web app on your internal network.
* [ngrok](https://ngrok.com/) - proprietary cloud-based reverse proxy. You will only need to run a client alongside your web app. It has a free tier, but it is quite limited.
* [smee.io](https://smee.io) - free cloud-based webhook relay. You will only need to run a client alongside your web app. It  was designed specifically for webhooks. However, on the stream I couldn't get it working.

Technically, all of the above solutions add a security hole to your infrastructure. So evaluate the risks with your security teams. I'd probably recommend to use a messenger offering websockets instead of webhooks.

Webex Teams specifically has two features which I believe address some of the problems mentioned above:
* [WebSockets support](https://developer.webex.com/blog/using-websockets-with-the-webex-javascript-sdk) - as of March, 2020, it's implemented in their JavaScript SDK, but I couldn't find any document describing the specification so I could re-implement this in other languages.
* [Buttons and Cards](https://developer.webex.com/docs/api/guides/cards) - those are essentially web forms, which significantly simplify data input and incoming message processing.


## Repository
#### network_overwatch folder
Python module containing the source code of Starlette app to receive and process events (webhooks) from Webex Teams.
Content:
* webex_teams.py - async Webex Teams REST API wrapper built using httpx library
* restconf.py - async RESTCONF API wrapper built using httpx library
* constants.py - contains connection details to the network devices and some other constants
* webhook_manager.py - contains some functions which create webhooks and handle incoming webhook events
* command_handler.py - contains functions that implement different commands for bots. Currently only one is available: handling of the command `vrf <device-name>`
* app.py - web app entrypoint which has routes, views and mapping between them.


## Instructions
1. Install and run ngrok on any port, e.g. 3000: `ngrok http 3000`
2. Set environmental variable `OVERWATCH_WEBEX_BOT_TOKEN` containing the token of your bot
3. Install dependencies using poetry: `poetry install` (python 3.7+)
4. Change connection details to your devices in `constants.py` (note, the device must be IOS-XE 16.7+ with RESTCONF enabled, otherwise you need to change the code to pull VRF list; you can use [DevNet Sandbox](https://devnetsandbox.cisco.com/RM/Diagram/Index/98d5a0fb-1b92-4b5b-abf6-a91e0ddba241?diagramType=Topology) to get IOS-XE virtual router)
5. Run the web app: `uvicorn network_overwatch.app:app --port 3000 --reload`
6. Check the bot operation by sending a message `vrf <device-name>` in a private chat or a group chat (@&lt;bot-name&gt; in that case), e.g. `vrf r1`. After a short delay, you will see a response with VRFs configured on that device.

## Stream recording
* ChatOps with Webex Team bot: https://youtu.be/5qMNMSVr2OU


## Resources
* Webex Teams webhooks: https://developer.webex.com/docs/api/guides/webhooks#filtering-webhooks
* Webex Teams buttons and cards: https://developer.webex.com/docs/api/guides/cards
* **frp** - open-source reverse proxy: https://github.com/fatedier/frp
* **ngrok** - proprietary cloud-based reverse proxy: https://ngrok.com/
* **starlette** - Python async web framework: https://www.starlette.io/
* **httpx** - Python sync/async HTTP/1.1 & HTTP/2 client: https://www.python-httpx.org/
* **errbot** - Python bot framework: https://errbot.readthedocs.io/en/latest/
* errbot webex teams backend: https://github.com/marksull/err-backend-cisco-webex-teams
