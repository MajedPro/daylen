# daylen 

A Python 3 script for generating an animation of day length isolines onto an
azimuthal map.

Since it's intended as a one-off script, there is no command-line interface
and control of the script is via hardcoded constants. Feel free to fork and
improve the interface, though.

The script requires the [astral](https://pypi.python.org/pypi/astral) module.
The base map was generated using [this](http://ns6t.net/azimuth/azimuth.html)
excellent service.

To generate the animation using ffmpeg:

	$ mkdir out
	$ ./daylen.py
	$ cd out
	$ ffmpeg -pattern_type glob -i '*.png' -vf scale=-2:720 -c:v libx264 -preset slow -crf 20 out.mp4

Results:

* [Sunrise - sunset](https://gfycat.com/CrispPlayfulAllosaurus)
* [Dawn - dusk](https://gfycat.com/YellowishEducatedBlackmamba)

