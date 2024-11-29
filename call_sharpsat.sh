#!/bin/bash
echo "hello1"
cd ../sharpsat-td/build/
./sharpSAT "$@"
echo "hello"