# daylen 

Script for generating an animation of day length isolines onto an
azimuthal map.

Since it's intended as a one-off script, there is no command-line interface
and control of the script is via hardcoded constants. Feel free to fork and
improve the interface, though.

To generate the animation using ffmpeg:

	$ mkdir out
	$ ./daylen.py
	$ cd out
	$ ffmpeg -pattern_type glob -i '*.png' -vf scale=-2:720 -c:v libx264 -preset slow -crf 20 out.mp4

[The result.](https://gfycat.com/CrispPlayfulAllosaurus)

