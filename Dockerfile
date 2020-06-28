FROM mono:6.8.0.96

WORKDIR /workdir

RUN apt-get update && apt-get install -y --allow-unauthenticated --no-install-recommends \
    ca-certificates zip file mono-devel libfreetype6 libopenal1 liblua5.1-0 libsdl2-2.0-0 \
    xdg-utils zenity wget make unzip python nsis imagemagick

