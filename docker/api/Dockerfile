FROM almalinux:10.2

RUN dnf update -y &&     dnf install -y procps git vim sudo
RUN echo "alias ls='ls --color=auto'" >> ~/.bashrc

RUN useradd -s /bin/bash worker &&     usermod -aG wheel worker &&     echo "worker ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER worker

ENV PATH="/home/worker/.local/bin:$PATH"

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

CMD [ "/bin/bash" ]

