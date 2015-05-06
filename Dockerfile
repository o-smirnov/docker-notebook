FROM ubuntu:14.04
MAINTAINER gijs@pythonic.nl

ENV DEBIAN_FRONTEND noninteractive

ADD apt.sources.list /etc/apt/sources.list
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y software-properties-common python-software-properties


## add radioastro PPA
RUN add-apt-repository -y ppa:radio-astro/main
RUN apt-get update


ADD debian_packages /
ADD python_packages /


# install debian packages
RUN apt-get -q update && cat /debian_packages | xargs apt-get -qy install && \
    apt-get -qy clean &&  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# install all python modules
RUN pip install -r /python_packages && \
    rm -rf /tmp/* /var/tmp/*


## Expose the ipython notebook port
EXPOSE 8888


## location of the Ipython notebooks.
VOLUME /notebooks
VOLUME /data

ADD notebooks /notebooks


## Run ipython notebook
CMD /usr/bin/python /usr/local/bin/ipython notebook --ip=* --no-browser --notebook-dir=/notebooks


