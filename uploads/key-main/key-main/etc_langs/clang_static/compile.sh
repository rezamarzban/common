
clang++ -std=c++17 -O2 -Wall \
        -target x86_64-linux-musl \
        -static -static-libstdc++ -static-libgcc \
        -o tracker tracker-lite.cpp