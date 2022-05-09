TinCanJS has a dependency on 'text-encoding', which uses a faulty way to detect whether it is running inside node. This results in it trying to run require() when inside a browser. As the dependency itself is deprecated by the author and TinCanJS doesn't seem to be maintained anymore, I doubt they'll get any official fixes. So I've just copied them here as a local dependency so we can patch it ourselves for now.

For more info on the node detection issue:
https://stackoverflow.com/a/11918368/18497739
