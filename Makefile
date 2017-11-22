
run:
	FLASK_APP=fatartifacts/web/server.py flask run

test-get:
	fatartifacts-rest-cli http://localhost:5000 root.bar:test:1.0:jre -u root:alpine -o-

test-put:
	fatartifacts-rest-cli http://localhost:5000 root.bar:test:1.0:jre C:/Users/niklas/Desktop/jiratime.py -u root:alpine

test-del:
	fatartifacts-rest-cli http://localhost:5000 root.bar:test:1.0:jre -d -u root:alpine
