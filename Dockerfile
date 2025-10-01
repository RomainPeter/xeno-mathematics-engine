FROM nixpkgs/nix:latest AS builder
WORKDIR /src
COPY . .
RUN nix build .#xme && ln -sf $(readlink -f result/bin/xme) /usr/local/bin/xme

FROM nixpkgs/nix:latest
COPY --from=builder /nix/store /nix/store
COPY --from=builder /usr/local/bin/xme /usr/local/bin/xme
ENTRYPOINT ["xme"]
CMD ["--help"]