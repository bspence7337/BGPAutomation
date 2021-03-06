# BGP Automation

Automate BGP looking glass queries through https://bgp.he.net. This will pull registered IP ranges and extract any newly discovered domains connected to those ranges.

## Requirements

Running Mac or Windows OS. These are the supported OS' Chrome Canary / Chrome Driver supports.

I also highly recommend you use virtualenv to manage the dependencies. If you're having trouble setting up the Chrome Driver and Canary, I recommend following this guide by Duo to get up and running: https://duo.com/decipher/driving-headless-chrome-with-python

### Note

I've only tested this on Mac OSX 10.13.X and do not plan to support Windows. If you are on Windows you will need to change the binary location and the chromedriver location.

## Setup

Download and install the Chrome Canary here: https://www.google.com/chrome/browser/canary.html

Download the Chrome Driver here and unzip it's contents into this repository: https://chromedriver.storage.googleapis.com/index.html?path=2.40/

Edit the settings.py file to point to your copy of Chrome Canary and Chrome Driver respectively.

Create a virtualenv for in this directory:

`virtualenv -p python3 env && source env/bin/activate`

Install the requirements:

`pip install -r requirements.txt`

That's it!

## Usage:

`./bgp.py -c "company name" -o "outputprefix"`

If -o is left out of the command line, only stdout is shown and no files are written.

## Additional Notes

BGP does have a query limit, so it may be possible you abort before you finish enumerating.

## Demo

`./bgp.py -c uber -o uber`

Example: Discover ip ranges and domain names associated with Uber.
	 If no -o is passed, only stdout is shown.

<a href="https://asciinema.org/a/VeRuALc9uqtS4uQ2PKG6O76Y8" target="_blank"><img src="https://asciinema.org/a/VeRuALc9uqtS4uQ2PKG6O76Y8.png" /></a>
