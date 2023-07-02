cf login -a https://api.cf.eu20.hana.ondemand.com
cf push WoRoMVG --vars-file ./.vars.yml


cf delete WoRoMVG

Needed:
.env file with
GMAPS_KEY=xyz
BOT_TOKEN=xyz

.vars.yml file with
GMAPS_KEY: xyz
BOT_TOKEN: xyz