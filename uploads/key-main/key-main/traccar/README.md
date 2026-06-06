* ssh into running container
* download a high version traccar : `https://github.com/traccar/traccar/releases/download/v${VERSION}/traccar-other-${VERSION}.zip`
* ```wget https://github.com/traccar/traccar/releases/download/v6.12.1/traccar-other-6.12.1.zip```
* unzip downloaded zip file 
* exec ```/usr/lib/jvm/jre-21/bin/java -jar tracker-server.jar conf/traccar.xml```
* navigate browser to port 8082
* set G19S device server and port to port 5023 of running container for correct protocol (each traccar listening port is for different protocol)