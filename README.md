# P2P Chat

A P2P chat application for a local network on Linux



## Notes

 - [Task](#Task)
 - [Launching the application](#Launching-the-application)
 - [Application limitations](#Limitations)
 - [Author](#Author)


## Task

Functional requirements: 
* the application enables communication between two instances over a network 
* the user enters their name upon launch 
* messages are exchanged in real time * each message contains the sender’s name 
* the application runs until the user exits 

Technical requirements: 
* language: C++ or Python 
* system: Linux 
* communication method and application architecture to be decided by the candidate 
* project placed in a GIT repository 
* the project should include a Readme or documentation in another format containing, amongst other things: build/run instructions and any limitations 
* the solution should be buildable/runable by a third party on two Linux machines.

## Running the application


**If the git package is not installed, you must install it**


On a Debian-based system
```bash
  sudo apt-get install git-all
```

On a Fedora system
```dash
dnf install git-all
```

Cloning the application locally
```bash
  git clone https://github.com/AlexFromPoland/Simple-P2PChat.git
```


Locate the project in the saved directory

```bash
  cd Simple-P2PChat
```

Running the application

```bash
  python3 P2Pchat.py
```

after launching the application: 
* you must enter the display name on the network
* new peers on the network are automatically added to the chat




## Application Limitations

* The application works **only on a local network** where users are connected to the same network

* No NAT traversal
* The broadcast port (by default UDP port 5000) must be accessible 
* The chat port (by default TCP port 4000) must be accessible
## Author

- [AlexFromPoland](https://github.com/AlexFromPoland)
