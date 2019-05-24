FROM webdevops/base:ubuntu-18.04
MAINTAINER sadisticsolutione@gmail.com

COPY . /script

RUN apt-get update \
 && apt-get install -y software-properties-common \
 && add-apt-repository -u -y ppa:alex-p/tesseract-ocr \
 && apt-get install -y python3-pip libgtk2.0-dev python-dev python-pip python3 tesseract-ocr libtesseract-dev tesseract-ocr-eng \
 && pip3 install -r /script/requirements.txt \
 && curl -L -o /usr/share/tesseract-ocr/4.00/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata_best/blob/master/eng.traineddata?raw=true

CMD tail -f /dev/null
WORKDIR /script
