# Multistage docker build, requires docker 17.05

# builder stage
FROM rust:latest as builder

# Install required packages
RUN rustup update && \
    set -ex && \
    apt-get update && \
    apt-get --no-install-recommends --yes install \
        clang \
        libclang-dev \
        llvm-dev \
        libncurses5 \
        libncursesw5 \
        cmake \
        git \
        libssl-dev

##
# Build Mugle and Mugle Wallet
WORKDIR /usr/src

# Clone mugle
RUN git clone https://github.com/mugleproject/mugle.git && \
    cd mugle && \
    git checkout v3.1.0 && \
    git fetch

# Clone mugle-wallet
RUN git clone https://github.com/mugleproject/mugle-wallet.git && \
    cd mugle-wallet && \
    git checkout v3.1.0 && \
    git fetch

# Build Mugle
WORKDIR /usr/src/mugle
RUN cargo build --release

# Generate configuration
RUN target/release/mugle server config



# Build Mugle Wallet
WORKDIR /usr/src/mugle-wallet

# Monkey Patch mugle-wallet
RUN sed -i -e 's/\.header(CONTENT_TYPE, "application\/json")//g'  controller/src/controller.rs
RUN sed -i -e 's/127\.0\.0\.1/0.0.0.0/g' config/src/types.rs

RUN cargo build --release




# runtime stage
FROM debian:10

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    locales \
    procps \
    libssl-dev \
    vim \
    telnet \
    curl \
    python3 \
    netcat \
    net-tools \
    libncursesw6 \
      && \
    apt-get autoremove -y && \
    rm -rf /var/cache/apt

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8 

ENV LANG en_US.UTF-8

COPY --from=builder /usr/src/mugle/target/release/mugle /usr/local/bin/
COPY --from=builder /usr/src/mugle-wallet/target/release/mugle-wallet /usr/local/bin/

COPY mugle-wallet.toml /usr/src/mugle-wallet/mugle-wallet.toml
COPY mugle-server.toml /usr/src/mugle/mugle-server.toml



# floonet ports
EXPOSE 13413
EXPOSE 13414
EXPOSE 13415
EXPOSE 13416
EXPOSE 13420

# mainnet ports
EXPOSE 3413
EXPOSE 3414
EXPOSE 3415
EXPOSE 3416
EXPOSE 3420

COPY run.sh /
COPY run-wallet.sh /
COPY libheath.py /
CMD ["/run.sh"]
