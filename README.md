Cameo is an OpenRA mod aiming to incorporate content from a wide variety of RTS and other games.

You can download binary releases [here](https://github.com/Zeruel87/Cameo-mod/releases/). However, due to the volume of content added, Cameo is extremely buggy, lacking in properly functioning features, and crash-prone, so updates vital to mod functionality are frequent. Thus, it is recommended that you clone this repository and build from source instead, so updating can be done with minimal effort through pulling.

The key scripts in this SDK are:

| Windows               | Linux / macOS            | Purpose
| --------------------- | ------------------------ | ------------- |
| make.cmd              | Makefile                 | Compiles the mod and fetches dependencies (including the OpenRA engine).
| launch-game.cmd       | launch-game.sh           | Launches the mod from the SDK directory.
| launch-server.cmd     | launch-server.sh         | Launches a dedicated server for the mod from the SDK directory.
| utility.cmd           | utility.sh         | Launches the OpenRA Utility for the mod.
| &lt;not available&gt; | packaging/package-all.sh | Generates release installers for the mod.

To launch Cameo from the development environment you must first compile the mod by running `make.cmd` (Windows), or opening a terminal in the SDK directory and running `make` (Linux / macOS).  You can then run `launch-game.cmd` (Windows) or `launch-game.sh` (Linux / macOS) to run your game.

For common questions regarding the OpenRA Mod SDK, please see the [FAQ](https://github.com/OpenRA/OpenRAModSDK/wiki/FAQ).

The OpenRA engine and SDK scripts are made available under the [GPLv3](https://github.com/OpenRA/OpenRA/blob/bleed/COPYING) license, and any executable code developed by a mod and loaded by the engine (i.e. custom mod DLLs, lua scripts) must be released under a compatible license.
