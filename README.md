https://github.com/rauldoe/cpsc551proj2 


pip3 install --user PyYAML
or 
pip install PyYAML
gem install xmlrpc 
gem install foreman
clear; python arithmetic_client.py

clear; foreman start -f Procfile.1
clear; foreman start -f Procfile.2


Ruby Debugging
https://dev.to/dnamsons/ruby-debugging-in-vscode-3bkj

gem install ruby-debug-ide
gem install debase

Run in Terminal
rdebug-ide --host 0.0.0.0 --port 1234 --dispatcher-port 26162 C:\temp\cpsc551proj2a\adapter.rb

Run in VSCode
clear; ruby adapter.rb -c alice.yaml