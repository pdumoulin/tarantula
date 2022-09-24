# tarantula
web server for home projects

### Install Service

Create directories app expects
```
$ mkdir logs
$ mkdir var
```

Register as service to auto start on boot
```
$ sudo cp ~/projects/tarantula/tarantula.service /lib/systemd/system/
$ sudo systemctl enable tarantula
```
