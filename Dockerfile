# Use the official ESP-IDF image
FROM espressif/idf:v5.2.2

# Set ESP-IDF path
ENV IDF_PATH="/opt/esp/idf/"

WORKDIR "/"

# RUN mkdir -p /fs
COPY src/main.py /main.py
COPY src/utils.py /utils.py
COPY src/log.py /log.py
COPY src/modulo_2fa.py /modulo_2fa.py
COPY src/modulo_ids.py /modulo_ids.py
# COPY boot.py /boot.py

RUN git clone https://github.com/earlephilhower/mklittlefs.git && \
  cd mklittlefs && \
  git submodule update --init && \
  make dist && \
  ./mklittlefs --version

RUN cd mklittlefs && \
  mkdir -p ~/fs && \
  cp /main.py ~/fs/main.py && \
  cp /utils.py ~/fs/utils.py && \
  cp /log.py ~/fs/log.py && \
  cp /modulo_2fa.py ~/fs/modulo_2fa.py && \
  cp /modulo_ids.py ~/fs/modulo_ids.py && \
  #  cp /boot.py ~/fs/boot.py && \
  ./mklittlefs -c ~/fs -b 4096 -p 256 -s 0x200000 /fs.bin


CMD ["/bin/bash"]
