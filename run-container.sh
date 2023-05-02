# purge any previous containers
rm database.db
rm -rf flask_session
docker rm -f $(docker container ls | grep hotorbot-container | cut -d " " -f 1)

docker build -t hotorbot-container .
docker run -d --restart always -p 5000:5000 -v /root/websites/hotorbot:/app hotorbot-container
